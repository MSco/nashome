import json
from pathlib import Path
from pydub import AudioSegment
from pytubefix import YouTube, Playlist, Channel, Stream, StreamQuery
import requests
import shutil
import subprocess
from unidecode import unidecode

from nashome.config.config import tmdb_api_token
from nashome.youtube.constants import LANGUAGES, STORED_VIDEOS_FILENAME

def download_youtube(urls:list[str], outdir:Path, audio_only:bool, language:str):
    stored_videos = read_stored_videos(outdir)
    for url in urls:
        if "@" in url:
            download_channel(channel_url=url, outdir=outdir, language=language, audio_only=audio_only, stored_videos=stored_videos)
        elif "playlist" in url:
            download_playlist(playlist_url=url, outdir=outdir, language=language, audio_only=audio_only, stored_videos=stored_videos)
        else:
            download_stream(yt=url, outdir=outdir, language=language, audio_only=audio_only)

    if stored_videos:
        write_stored_videos(outdir, stored_videos)

def download_channel(channel_url:str, outdir:str|Path, language:str, audio_only:bool, stored_videos:list[str]):
    print("Downloading channel")
    channel = Channel(channel_url, 'WEB', use_oauth=True, allow_oauth_cache=True)
    for playlist in channel.playlists:
        download_playlist(playlist_url=playlist.playlist_url, outdir=outdir, language=language, audio_only=audio_only, stored_videos=stored_videos)

def download_playlist(playlist_url:str, outdir:str|Path, language:str, audio_only:bool, stored_videos:list[str]):
    print(f"Downloading playlist {playlist_url}")
    playlist = Playlist(playlist_url, 'WEB', use_oauth=True, allow_oauth_cache=True)

    for video in playlist.videos:
        if video.video_id in stored_videos:
            continue
        download_stream(yt=video, outdir=outdir, language=language, audio_only=audio_only)
        stored_videos.append(video.video_id)


def download_stream(yt:str|YouTube, outdir:str|Path, language:str, audio_only:bool):
    # differentiate between url and YouTube object
    if isinstance(yt, str):
        yt = YouTube(yt, 'WEB', use_oauth=True, allow_oauth_cache=True)

    # define output file name
    output_filename = generate_filename(yt=yt, audio_only=audio_only)

    # create output directory if not exists
    outdir.mkdir(parents=True, exist_ok=True)

    # progress output
    print(f"Downloading {"audio" if audio_only else "video"} {yt.title}")

    if audio_only:
        download_audio(yt=yt, outdir=outdir, outfilename=output_filename)
        return True

    if outdir/output_filename in outdir.iterdir():
        print(f"File {output_filename} already exists.")
        return False

    # check if extra audio tracks are available
    audio_tracks = yt.streams.get_extra_audio_track()

    if audio_tracks:
        download_audio_and_video(yt=yt, outdir=outdir, outfilename=output_filename, audio_tracks=audio_tracks, language=language)
    else:
        # Download video
        yt.streams.order_by("resolution").last().download(output_path=str(outdir), filename=output_filename)

    return True

def generate_filename(yt:YouTube, audio_only:bool):
    dict_series = {
        'Pokemon': 60572,
    }
    suffix = 'm4a' if audio_only else 'mp4'
    output_filename = None
    for title_name in dict_series.keys():
        if title_name.lower() in unidecode(yt.title).lower():
            episode, season = find_episode_and_season(title=yt.title, series_id=dict_series[title_name])
            if not episode or not season:
                continue
            output_filename = f'{title_name} - s{season:02d}e{episode:03d}.{suffix}'
            break
    else:
        output_filename = f'{yt.title}.{suffix}'

    return output_filename


def download_audio(yt:str|YouTube, outdir:str|Path, outfilename:str):
    # define output directory
    temporary_directory = Path(outdir) / 'tmp' 

    # Download audio and convert to mp3
    yt.streams.get_audio_only().download(output_path=str(temporary_directory), filename=outfilename)
    audio = AudioSegment.from_file(str(temporary_directory/outfilename), format="m4a")
    audio.export((outdir/outfilename).with_suffix('.mp3'), format="mp3")

    # Clean up
    shutil.rmtree(temporary_directory)

def download_audio_and_video(yt:YouTube, outdir:str|Path, outfilename:str, audio_tracks:StreamQuery, language:str):
    # define temporary directory
    temporary_directory = Path(outdir) / 'tmp' 

    # define language name if not specified
    if language:
        if language in LANGUAGES:
            language:Language = LANGUAGES[LANGUAGES.index(language)]
        else:
            print(f"Language {language} not found. Available languages are: {LANGUAGES}")
            return False
    else:
        language = LANGUAGES[0] # default: German

    # Download audio track
    audio_track_list = [yt.streams.get_default_audio_track(), audio_tracks.order_by('abr').desc()]
    for audio_track_listelement in audio_track_list:
        for stream in audio_track_listelement:
            stream:Stream
            if any(x in stream.audio_track_name.lower() for x in language.long) or any(x == stream.audio_track_name.lower() for x in language.short):
                stream.download(output_path=str(temporary_directory))
                break
        else:
            continue
        break
    else:
        print("Specified audio track found.")
        return False

    # Download video
    yt.streams.order_by("resolution").filter(mime_type="video/mp4").last().download(output_path=str(temporary_directory))

    # Find audio and video file
    audio_file, video_file = None, None
    for file in temporary_directory.iterdir():
        if file.suffix == '.m4a':
            audio_file = file
        elif file.suffix == '.mp4':
            video_file = file

    # Merge audio and video
    if audio_file and video_file:
        merge_audio_and_video(video_file, audio_file, outdir / outfilename)

    # Clean up
    shutil.rmtree(temporary_directory)

def merge_audio_and_video(video_file:Path, audio_file:Path, outpath:Path):
    # define ffmpeg command
    command = [
        'ffmpeg',
        '-i', video_file,
        '-i', audio_file,
        '-c:v', 'copy',  # Copy the video stream without re-encoding
        '-strict', 'experimental',  # Allow experimental codecs if needed
        '-map', '0:v:0',  # Select the first video stream from the first input
        '-map', '1:a:0',  # Select the first audio stream from the second input
        '-loglevel', 'error',  # Suppress output
        outpath
    ]

    # run ffmpeg command
    print(f"Merging audio and video using {command[0]}")
    subprocess.run(command, check=True)

def find_episode_and_season(title:str, series_id:int):
    # https://developer.themoviedb.org/reference/search-tv
    # https://developer.themoviedb.org/reference/tv-season-details

    num_seasons = 25
    for season in range(1, num_seasons+1):
        url = f"https://api.themoviedb.org/3/tv/{series_id}/season/{season}?language=en-US"
        headers = {
                    "accept": "application/json",
                    "Authorization": f"Bearer {tmdb_api_token}"
                }
        response = requests.get(url, headers=headers)
        for episode in response.json()['episodes']:
            tmdb_episode_name = unidecode(episode['name']).lower()
            title = unidecode(title).lower()
            if tmdb_episode_name in title or any([part in tmdb_episode_name for part in map(str.strip,title.split("|"))]):
                print(f"Found {episode['name']} as episode {episode['episode_number']} and season {season} in TMDB.")
                return episode['episode_number'], episode['season_number']
    return None, None

def read_stored_videos(outdir:Path|str) -> list[str]:
    stored_videos_path = Path(outdir) / STORED_VIDEOS_FILENAME
    if not stored_videos_path.exists():
        return []
    return json.load(open(stored_videos_path, 'r'))

def write_stored_videos(outdir:Path|str, stored_videos:list[str]) -> None:
    stored_videos_path = Path(outdir) / STORED_VIDEOS_FILENAME
    json.dump(stored_videos, open(stored_videos_path, 'w'))