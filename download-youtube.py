#!/usr/bin/env python
import argparse
from pathlib import Path
from pydub import AudioSegment
from pytubefix import YouTube, Playlist, Stream
import re
import requests
import shutil
import subprocess

class Language():
    def __init__(self, long:list[str], short:list[str]):
        self.long = list(map(str.lower, long))
        self.short = list(map(str.lower, short))

    def __str__(self):
        return self.long + self.short

    def __repr__(self):
        return self.long

    def __eq__(self, other:str):
        return other.lower() in self

    def __contains__(self, other:str):
        return other.lower() in self.long or other.lower() in self.short
    
LANGUAGES:list[Language] = [
    Language(['german', 'deutsch'], ['deu', 'ger', 'de']),
    Language(['english', 'englisch'], ['en', 'eng', 'us']),
    Language(['italian', 'italienisch'], ['it', 'ita']),
    Language(['spanish', 'spanisch'], ['spa', 'es']),
    Language(['portuguese', 'portugiesisch'], ['pt', 'por']),
    Language(['french', 'französisch'], ['fr', 'fra']),
    Language(['russian', 'russisch'], ['ru', 'rus']),
    Language(['chinese', 'chinesisch'], ['zh', 'chi']),
    Language(['japanese', 'japanisch'], ['ja', 'jpn']),
    Language(['korean', 'koreanisch'], ['ko', 'kor']), 
    Language(['arabic', 'arabisch'], ['ar', 'ara']),
    Language(['turkish', 'türkisch'], ['tr', 'tur']),
    Language(['hindi'], ['hi', 'hin']),
    Language(['bengali'], ['bn', 'ben']),
    Language(['urdu'], ['ur', 'urd']),
    Language(['indonesian'], ['id', 'ind']),
    Language(['malay'], ['ms', 'may']),
    Language(['vietnamese'], ['vi', 'vie']),
    Language(['thai'], ['th', 'tha']),
    Language(['swahili'], ['sw', 'swa']),
]

def download_playlist(playlist_url:str, outdir:str|Path, language:str, audio_only:bool):
    print("Downloading playlist")
    playlist = Playlist(playlist_url, 'WEB', use_oauth=True, allow_oauth_cache=True)
    for video in playlist.videos:
        download_stream(yt=video, outdir=outdir, language=language, audio_only=audio_only)

def download_stream(yt:str|YouTube, outdir:str|Path, language:str, audio_only:bool):
    # differentiate between url and YouTube object
    if isinstance(yt, str):
        yt = YouTube(yt, 'WEB', use_oauth=True, allow_oauth_cache=True)

    print(f"Downloading {"audio" if audio_only else "video"} {yt.title}")

    # define output file name
    dict_regex = {
        'Pokemon': re.compile(r'.*FULL EPISODE (\d+) \| Season (\d+)'),
    }
    suffix = 'm4a' if audio_only else 'mp4'
    output_filename = None
    for title_name in dict_regex.keys():
        regex = dict_regex[title_name]
        match_episode = regex.match(yt.title)
        if match_episode is not None:
            episode, season = map(int, match_episode.groups())
            output_filename = f'{title_name} - s{season:02d}e{episode:03d}.{suffix}'
            break
    else:
        output_filename = f'{yt.title}.{suffix}'

    if audio_only:
        temporary_directory = Path(outdir) / 'tmp' 
        yt.streams.get_audio_only().download(output_path=str(temporary_directory), filename=output_filename)
        audio = AudioSegment.from_file(str(temporary_directory/output_filename), format="m4a")
        audio.export((outdir/output_filename).with_suffix('.mp3'), format="mp3")
        shutil.rmtree(temporary_directory)
        return True

    # create output directory if not exists
    outdir.mkdir(parents=True, exist_ok=True)

    if outdir/output_filename in outdir.iterdir():
        print(f"File {output_filename} already exists.")
        return False

    # check if extra audio tracks are available
    audio_tracks = yt.streams.get_extra_audio_track()

    if audio_tracks:
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
            merge_audio_and_video(video_file, audio_file, outdir / output_filename)

        # Clean up
        shutil.rmtree(temporary_directory)
    else:
        # Download video
        yt.streams.order_by("resolution").last().download(output_path=str(outdir), filename=output_filename)

    return True

def merge_audio_and_video(video_file:Path, audio_file:Path, outpath:Path):
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
    print(f"Merging audio and video using {command[0]}")
    subprocess.run(command, check=True)
def main():
    # argument parsing
    parser = argparse.ArgumentParser(description="Download movie(s) from YouTube movie/playlist url.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('urls', type=str, nargs='+', help="YouTube movie/playlist url(s).")
    parser.add_argument('outdir', type=Path, help="Path to the output directory.")
    parser.add_argument('-a', "--audio-only", action='store_true', help="If specified, only the audio stream will be downloaded and converted to mp3.")
    parser.add_argument('-l', "--language", type=str, help="If specified, the video will be re-dubbed with an extra audio stream in given language, if available (default: German).")
    
    args = parser.parse_args()
    for url in args.urls:
        if "playlist" in url:
            download_playlist(playlist_url=url, outdir=args.outdir, language=args.language, audio_only=args.audio_only)
        else:
            download_stream(yt=url, outdir=args.outdir, language=args.language, audio_only=args.audio_only)

if __name__ == "__main__":
    main()
