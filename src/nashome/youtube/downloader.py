from pathlib import Path
from pydub import AudioSegment
from pytubefix import YouTube, Playlist, Channel, Stream, StreamQuery
import shutil

from nashome.utils.constants import LANGUAGE_LIST, STORED_VIDEOS_FILENAME
from nashome.youtube.database import read_stored_videos, write_stored_videos
from nashome.youtube.language import Language
from nashome.utils.movie import merge_audio_and_video
from nashome.utils.renamer import build_filename_from_title

def download_youtube(urls:list[str], outdir:Path, audio_only:bool, language:str, try_all_seasons:bool, min_length:int):
    stored_videos = read_stored_videos(outdir)
    for url in urls:
        if "@" in url:
            download_channel(channel_url=url, outdir=outdir, language=language, try_all_seasons=try_all_seasons, audio_only=audio_only, stored_videos=stored_videos, min_length=min_length)
        elif "playlist" in url:
            download_playlist(playlist_url=url, outdir=outdir, language=language, try_all_seasons=try_all_seasons, audio_only=audio_only, stored_videos=stored_videos, min_length=min_length)
        else:
            download_stream(yt=url, outdir=outdir, language=language, try_all_seasons=try_all_seasons, audio_only=audio_only, min_length=min_length)

    if stored_videos:
        stored_videos_path = outdir / STORED_VIDEOS_FILENAME
        old_videos = read_stored_videos(outdir)
        if len(old_videos) == len(stored_videos):
            return
        
        print(f"Writing {stored_videos_path}")
        write_stored_videos(stored_videos=stored_videos, outpath=stored_videos_path)

def download_channel(channel_url:str, outdir:str|Path, language:str, try_all_seasons:bool, audio_only:bool, stored_videos:list[str], min_length:int):
    channel = Channel(channel_url, 'WEB', use_oauth=True, allow_oauth_cache=True)
    print(f"Downloading channel {channel.channel_name}")
    for playlist in channel.playlists:
        download_playlist(playlist_url=playlist.playlist_url, outdir=outdir, language=language, try_all_seasons=try_all_seasons, audio_only=audio_only, stored_videos=stored_videos, min_length=min_length)
    print("Channel done.")

def download_playlist(playlist_url:str, outdir:str|Path, language:str, try_all_seasons:bool, audio_only:bool, stored_videos:list[str], min_length:int):
    playlist = Playlist(playlist_url, 'WEB', use_oauth=True, allow_oauth_cache=True)
    print(f"Downloading playlist {playlist.title}")

    for video in playlist.videos:
        if video.video_id in stored_videos:
            continue
        result = download_stream(yt=video, outdir=outdir, language=language, try_all_seasons=try_all_seasons, audio_only=audio_only, min_length=min_length)
        if result:
            stored_videos.append(video.video_id)
    print("Playlist done.")


def download_stream(yt:str|YouTube, outdir:str|Path, language:str, try_all_seasons:bool, audio_only:bool, min_length:int):
    # differentiate between url and YouTube object
    if isinstance(yt, str):
        yt = YouTube(yt, 'WEB', use_oauth=True, allow_oauth_cache=True)

    # check length of video
    if yt.length < min_length * 60:
        print(f"Video {yt.title} is shorter than {min_length} minutes. Skipping.")
        return False

    # check if extra audio tracks are available
    audio_tracks = yt.streams.get_extra_audio_track()
    language_code = "en-US" if audio_tracks else "de-DE"

    # define output file name
    output_filename, episode_name = build_filename_from_title(title=yt.title, suffix='m4a' if audio_only else 'mp4', language_code=language_code, try_all_seasons=try_all_seasons)

    # check if file already exists
    if (outdir/output_filename).is_file():
        print(f"File {output_filename} already exists.")
        return False
    
    # create output directory
    outdir.mkdir(parents=True, exist_ok=True)
    
    # progress output
    print(f"Downloading {"audio" if audio_only else "video"} {yt.title}")
    
    if audio_only:
        download_audio(yt=yt, outdir=outdir, outfilename=output_filename)
        return True

    result = download_audio_and_video(yt=yt, outdir=outdir, outfilename=output_filename, audio_tracks=audio_tracks, episode_name=episode_name, language=language)

    print(f"Stream done.")
    return result

def download_audio(yt:str|YouTube, outdir:str|Path, outfilename:str):
    # define output directory
    temporary_directory = Path(outdir) / 'tmp' 

    # Download audio and convert to mp3
    yt.streams.get_audio_only().download(output_path=str(temporary_directory), filename=outfilename)
    audio = AudioSegment.from_file(str(temporary_directory/outfilename), format="m4a")
    audio.export((outdir/outfilename).with_suffix('.mp3'), format="mp3")

    # Clean up
    shutil.rmtree(temporary_directory)

def download_audio_and_video(yt:YouTube, outdir:str|Path, outfilename:str, audio_tracks:StreamQuery, episode_name:str, language:str):
    # define temporary directory
    temporary_directory = Path(outdir) / 'tmp' 

    # define language name if not specified
    if language:
        if language in LANGUAGE_LIST:
            language:Language = LANGUAGE_LIST[LANGUAGE_LIST.index(language)]
        else:
            print(f"Language {language} not found. Available languages are: {LANGUAGE_LIST}")
            return False
    else:
        language = LANGUAGE_LIST[0] # default: German

    # Download audio track
    audio_track_list = [yt.streams.get_default_audio_track().order_by('abr').desc(), audio_tracks.order_by('abr').desc()]
    for audio_track_listelement in audio_track_list:
        for stream in audio_track_listelement:
            stream:Stream
            if (not audio_tracks) or (any(x in stream.audio_track_name.lower() for x in language.long) or any(x == stream.audio_track_name.lower() for x in language.short)):
                stream.download(output_path=str(temporary_directory))
                break
        else:
            continue
        break
    else:
        print("Specified audio track not found.")
        return False

    # Download video
    yt.streams.order_by("resolution").filter(mime_type="video/mp4").last().download(output_path=str(temporary_directory))

    # Merge audio and video
    return merge_audio_and_video(temporary_directory, outdir / outfilename, episode_name)
