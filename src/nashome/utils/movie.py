import ffmpeg
from pathlib import Path
import shutil

def merge_audio_and_video(indir:Path, outpath:Path):
    # Find audio and video file
    audio_file, video_file = None, None
    for file in indir.iterdir():
        if file.suffix == '.m4a':
            audio_file = file
        elif file.suffix == '.mp4':
            video_file = file

    if not audio_file or not video_file:
        return False

    video_input = ffmpeg.input(str(video_file))
    audio_input = ffmpeg.input(str(audio_file))

    ffmpeg.output(video_input, audio_input, str(outpath), vcodec='copy', acodec='aac', strict='experimental', loglevel="error").run()

    # Clean up
    shutil.rmtree(indir)