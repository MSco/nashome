from logging import info
from pathlib import Path
from pydub import AudioSegment
import shutil
from yt_dlp import YoutubeDL

from nashome.utils.constants import LANGUAGE_LIST, STORED_VIDEOS_FILENAME
from nashome.youtube.database import read_stored_videos, write_stored_videos
from nashome.youtube.language import Language
from nashome.utils.movie import merge_audio_and_video
from nashome.utils.renamer import build_filename_from_title

def build_ydl_base_opts():
    return {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
    }

def build_ydl_download_opts(outpath: Path, audio_only: bool, language:str):
    if language in LANGUAGE_LIST:
        language_code = LANGUAGE_LIST[LANGUAGE_LIST.index(language)].code
    else:
        language_code = "de-DE" # default to German if language not found

    if audio_only:
        return {
            "format": f"ba[language={language_code}]/ba",
            "outtmpl": str(outpath),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3"
            }],
            "js_runtimes": {"node": {}},
            "remote_components": {"ejs:github"},
        }

    return {
        "format": f"bv*[ext=mp4]+ba[ext=m4a][language={language_code}]/b[ext=mp4]",
        "outtmpl": str(outpath),
        "js_runtimes": {"node": {}},
        "remote_components": {"ejs:github"},
    }

def download_youtube(urls:list[str], outdir:Path, audio_only:bool, language:str, try_all_seasons:bool, min_length:int, external_audio_dir:Path|None, audio_offset:float):
    stored_videos = read_stored_videos(outdir)
    for url in urls:
        if "@" in url:
            download_channel(channel_url=url, outdir=outdir, language=language, try_all_seasons=try_all_seasons, audio_only=audio_only, stored_videos=stored_videos, min_length=min_length, external_audio_dir=external_audio_dir, audio_offset=audio_offset)
        elif "playlist" in url:
            download_playlist(playlist_url=url, outdir=outdir, language=language, try_all_seasons=try_all_seasons, audio_only=audio_only, stored_videos=stored_videos, min_length=min_length, external_audio_dir=external_audio_dir, audio_offset=audio_offset)
        else:
            download_stream(video_url=url, outdir=outdir, language=language, try_all_seasons=try_all_seasons, audio_only=audio_only, min_length=min_length, external_audio_dir=external_audio_dir, audio_offset=audio_offset)

    if stored_videos:
        stored_videos_path = outdir / STORED_VIDEOS_FILENAME
        old_videos = read_stored_videos(outdir)
        if len(old_videos) == len(stored_videos):
            return
        
        print(f"Writing {stored_videos_path}")
        write_stored_videos(stored_videos=stored_videos, outpath=stored_videos_path)

def download_channel(channel_url:str, outdir:str|Path, language:str, try_all_seasons:bool, audio_only:bool, stored_videos:list[str], min_length:int, external_audio_dir:Path|None, audio_offset:float):
    print(f"Downloading channel {channel_url}")

    with YoutubeDL(build_ydl_base_opts()) as ydl:
        info = ydl.extract_info(channel_url, download=False)

    channel_id = info["entries"][0]["id"]
    uploads_playlist = "UU" + channel_id[2:]
    playlist_url = f"https://www.youtube.com/playlist?list={uploads_playlist}"
    download_playlist(playlist_url=playlist_url, outdir=outdir, language=language, try_all_seasons=try_all_seasons, audio_only=audio_only, stored_videos=stored_videos, min_length=min_length, external_audio_dir=external_audio_dir, audio_offset=audio_offset)
    print("Channel done.")

def download_playlist(playlist_url:str, outdir:str|Path, language:str, try_all_seasons:bool, audio_only:bool, stored_videos:list[str], min_length:int, external_audio_dir:Path|None, audio_offset:float):
    print(f"Downloading playlist {playlist_url}")

    with YoutubeDL(build_ydl_base_opts()) as ydl:
        playlist = ydl.extract_info(playlist_url, download=False)


    for entry in playlist["entries"]:
        if not entry:
            continue

        video_id = entry["id"]
        if video_id in stored_videos:
            continue
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        result = download_stream(video_url=video_url, outdir=outdir, language=language, try_all_seasons=try_all_seasons, audio_only=audio_only, min_length=min_length, external_audio_dir=external_audio_dir, audio_offset=audio_offset)
        if result:
            stored_videos.append(video_id)
    print("Playlist done.")


def download_stream(video_url:str, outdir:str|Path, language:str, try_all_seasons:bool, audio_only:bool, min_length:int, external_audio_dir:Path|None, audio_offset:float):
    meta_opts = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
        "extract_flat": True,
        "js_runtimes": {"node": {}},
        "remote_components": {"ejs:github"},
        "ignoreerrors": True,
    }

    try:
        with YoutubeDL(meta_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
    except Exception as exc:
        print(f"Could not read metadata for {video_url}. Skipping. ({exc})")
        return False

    if not info:
        print(f"Could not read metadata for {video_url}. Skipping.")
        return False

    # check video length, skip if shorter than min_length
    duration = info.get("duration") or 0
    title = info.get("title") or video_url
    if duration < min_length * 60:
        print(f"Video {title} is shorter than {min_length} minutes. Skipping.")
        return False

    # check if extra audio tracks are available
    audio_formats = [
    f for f in info.get("formats", [])
    if f.get("acodec") != "none"
    ]
    available_languages = {
        f.get("language")
        for f in audio_formats
        if f.get("language")
    }
    # if extra audio tracks are available, the stream title name will be in English
    language_code = "en-US" if available_languages else "de-DE"

    # define output file name
    output_filename, episode_name = build_filename_from_title(title=info.get("title"), suffix='m4a' if audio_only else 'mp4', language_code=language_code, try_all_seasons=try_all_seasons)

    # check if file already exists
    if (outdir/output_filename).is_file():
        print(f"File {output_filename} already exists.")
        return True
    
    # create output directory
    outdir.mkdir(parents=True, exist_ok=True)
    
    # progress output
    print(f"Downloading {"audio" if audio_only else "video"} {title}")
    
    # external audio dir is only relevant if there are extra audio tracks available and we do not find the specified language in those tracks.
    if available_languages and external_audio_dir:
        language_code = LANGUAGE_LIST[LANGUAGE_LIST.index(language)].code

        if not language_code in available_languages:
            external_audio_dir = external_audio_dir
        else:
            external_audio_dir = None 
    else:
        external_audio_dir = None

    result = download_audio_and_video(video_url=video_url, outdir=outdir, outfilename=output_filename, audio_only=audio_only, episode_name=episode_name, language=language, external_audio_dir=external_audio_dir, audio_offset=audio_offset)

    print(f"Stream done.")
    return result

def _find_external_audio(episode_key:str, external_audio_dir:Path) -> Path|None:
    """Search recursively for an external audio file whose name contains the episode_key.
    Acceptable suffixes: .m4a .mp3 .aac .wav .mkv .mp4 (latter two will be demuxed). Returns first sorted match or None."""
    if not external_audio_dir or not external_audio_dir.is_dir():
        return None
    candidates: list[Path] = []
    for p in external_audio_dir.rglob('*'):
        if not p.is_file():
            continue
        if episode_key in p.name and p.suffix.lower() in ['.m4a', '.mp3', '.aac', '.wav', '.mkv', '.mp4']:
            candidates.append(p)
    if not candidates:
        return None
    return sorted(candidates)[0]

def _extract_or_convert_audio(source:Path, target_dir:Path, target_stem:str) -> Path|None:
    """Create a .m4a audio file in target_dir from source (copy or extract first audio stream)."""
    target_dir.mkdir(parents=True, exist_ok=True)
    out_audio = target_dir / f"{target_stem}.m4a"
    if source.suffix.lower() in ['.m4a']:
        shutil.copy(source, out_audio)
        return out_audio
    # Use ffmpeg to extract/convert
    import subprocess
    cmd = [
        'ffmpeg', '-i', str(source), '-vn', '-acodec', 'aac', '-b:a', '192k', '-y', str(out_audio)
    ]
    print(f"Extracting/converting external audio: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        print(f"Failed to extract audio from {source}:\n{result.stdout}")
        return None
    return out_audio

def download_audio_and_video(video_url:str, outdir:str|Path, outfilename:str, audio_only:bool, episode_name:str, language:str, external_audio_dir:Path|None, audio_offset:float):
    # define temporary directory
    temporary_directory = Path(outdir) / 'tmp' 

    # define download options
    download_opts = build_ydl_download_opts(Path(temporary_directory) / outfilename, audio_only, language)

    # Download video from YouTube
    try:
        with YoutubeDL(download_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        print(f"Failed to download from {video_url}: {e}")
        return False

    if external_audio_dir:
        import re
        stem = Path(outfilename).stem
        m = re.search(r"(.+ - s\d{2}e\d{3})", stem)
        if m:
            episode_key = m.group(1)
            external_audio = _find_external_audio(episode_key, external_audio_dir)
            if external_audio:
                print(f"Found external audio for '{episode_key}': {external_audio}")
                converted = _extract_or_convert_audio(external_audio, temporary_directory, Path(outfilename).stem)
                if not converted:
                    print("External audio conversion failed; aborting this stream.")
                    return False
                # Merge audio and video with offset
                return merge_audio_and_video(temporary_directory, outdir / outfilename, episode_name, audio_offset=audio_offset)
            else:
                print("External audio not found; aborting this stream.")
                return False
        else:
            print("Could not derive episode key pattern from filename; aborting this stream.")
            return False
    else:
        # Move downloaded file to final location (or merge if audio_only is False)
        shutil.move(temporary_directory / outfilename, outdir / outfilename)
        shutil.rmtree(temporary_directory)
        return True