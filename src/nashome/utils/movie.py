import cv2
import ffmpeg
import json
from pathlib import Path
import shutil
import subprocess

from nashome.utils.constants import TEMPLATE_START_DIRNAME, TEMPLATE_END_DIRNAME
from nashome.utils.eit import EitContent

def merge_audio_and_video(indir:Path, outpath:Path, episode_name:str=None):
    # Find audio and video file
    audio_file, video_file = None, None
    for file in indir.iterdir():
        if file.suffix == '.m4a':
            audio_file = file
        elif file.suffix == '.mp4':
            video_file = file

    if not audio_file or not video_file:
        return False

    # video_input = ffmpeg.input(str(video_file))
    # audio_input = ffmpeg.input(str(audio_file))

    # ffmpeg.output(video_input, audio_input, str(outpath), vcodec='copy', acodec='aac', strict='experimental', language="ger", loglevel="error").run()

    command = [
        'ffmpeg',
        '-i', video_file,
        '-i', audio_file,
        '-c:v', 'copy',  # Copy the video stream without re-encoding
        '-strict', 'experimental',  # Copy the audio stream without re-encoding
        '-map', '0:v:0',  # Select the first video stream from the first input
        '-map', '1:a:0',  # Select the first audio stream from the second input
        '-metadata:s:a:0', 'language=ger',  # Set the language of the audio stream,
        '-metadata', f'title={episode_name if episode_name else ""}',  # Set the title of the output file
        '-loglevel', 'error',  # Suppress output
        outpath
    ]

    # run ffmpeg command
    print(f"Merging audio and video using {command[0]}")
    process = subprocess.run(command, check=True)

    # Clean up
    shutil.rmtree(indir)
    return process.returncode == 0

def find_template(frame:cv2.typing.MatLike, template:cv2.typing.MatLike, threshold:float=0.8) -> bool:
    """
    Searches for the template in the given frame.
    Returns True if the template is found with a confidence above the threshold.
    """
    result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    return max_val >= threshold

def check_template_root_directory(template_root_directory:Path) -> tuple[list[Path], list[Path]]:
    """
    Checks if the template root directory exists and contains start and end template directories.

    Returns the start and end template image paths if they exist, otherwise None.
    """
    start_template_dir = template_root_directory / TEMPLATE_START_DIRNAME
    end_template_dir = template_root_directory / TEMPLATE_END_DIRNAME

    if not start_template_dir.is_dir() or not end_template_dir.is_dir():
        print("Error: Could not find start or end template directory.")
        return None, None
    
    start_template_image_paths = sorted([f for f in start_template_dir.iterdir() if f.is_file() and f.suffix.lower() in ['.png', '.jpg']])
    end_template_image_paths = sorted([f for f in end_template_dir.iterdir() if f.is_file() and f.suffix.lower() in ['.png', '.jpg']])

    return start_template_image_paths, end_template_image_paths

def cut_video(video_path:str|Path, template_dir:str|Path, outdir:str|Path, offset_minutes:float, movie_length_minutes:float) -> bool:
    # Create Path objects
    start_template_dir = Path(template_dir)/TEMPLATE_START_DIRNAME
    end_template_dir = Path(template_dir)/TEMPLATE_END_DIRNAME

    # Check if the directories exist
    if not start_template_dir.is_dir() or not end_template_dir.is_dir():
        print("Error: Could not find start or end template directory.")
        return False

    # Get the template image paths
    start_template_image_paths, end_template_image_paths = check_template_root_directory(template_root_directory=Path(template_dir))

    # Check if the template images exist
    if not start_template_image_paths or not end_template_image_paths:
        print("Error: Could not find start or end template images.")
        return False

    if not movie_length_minutes:
        print(f"Searching for movie length from EIT for {video_path}")
        eit = EitContent(video_path)
        duration = eit.getEitDuration()
        if duration:
            movie_length_minutes = duration[0] * 60 + duration[1] + duration[2] / 60 
            print(f"Found move length from EIT: {movie_length_minutes} minutes")
            movie_length_minutes -= 1

    # Load the template images in grayscale
    start_templates = [cv2.imread(f, cv2.IMREAD_GRAYSCALE) for f in start_template_image_paths]
    end_templates = [cv2.imread(f, cv2.IMREAD_GRAYSCALE) for f in end_template_image_paths]

    # Open the video file
    cap = cv2.VideoCapture(video_path)

    # Check if the video opened successfully
    if not cap.isOpened():
        print("Error: Could not open video.")
        return False
    
    start_frame_index = None
    end_frame_index = None

    # Get the frames per second (fps) of the video
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Calculate the frame index to start at
    frame_index = int(offset_minutes * 60 * fps)
    if frame_index:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    key_frame_size = 0.6*fps
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert the frame to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Check for the start template
        if start_frame_index is None and any([find_template(gray_frame, t) for t in start_templates]):
            start_frame_index = frame_index-frame_index%key_frame_size+key_frame_size
            print(f"Start template found at frame {start_frame_index}")
            if movie_length_minutes:
                frame_index += int(60 * fps * (movie_length_minutes))
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

        # Check for the end template
        elif start_frame_index is not None and end_frame_index is None:
            if any([find_template(gray_frame, t) for t in end_templates]):
                end_frame_index = frame_index-frame_index%key_frame_size+key_frame_size
                print(f"End template found at frame {end_frame_index}")
                break

        frame_index += 1

    # Release the video capture object
    cap.release()

    # Ensure both templates were found
    if start_frame_index is None or end_frame_index is None:
        print("Error: Could not find both templates in the video.")
        return False

    # Calculate start and end times in seconds
    start_time = start_frame_index / fps
    end_time = end_frame_index / fps

    print(f"Start time: {start_time} seconds")
    print(f"End time: {end_time} seconds")

    # Use FFmpeg to trim the video
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    video_path = Path(video_path)
    outpath = outdir / f"{video_path.name}"
    ffmpeg.input(video_path, ss=start_time, to=end_time).output(str(outpath), c='copy').run(overwrite_output=True)

    print(f"Trimmed video saved to {outdir}")
    return True

def get_smallest_subtitle_track(input_file) -> int:
   """Ermittelt die kleinste Untertitelspur in der Datei mit ffprobe."""
   cmd = ["ffprobe", "-v", "error", "-select_streams", "s", "-show_streams", "-of", "json", input_file]
   result = subprocess.run(cmd, capture_output=True, text=True)
   
   if result.returncode != 0:
       print("Fehler beim Analysieren der Datei.")
       return None, 0
   
   streams = json.loads(result.stdout).get("streams", [])
   
   if not streams:
       return None, 0
   
   print(f"Found {len(streams)} subtitle streams.")
   smallest_track = min(streams, key=lambda s: float(s.get("duration")))
   print(f"Selected subtitle stream index: {smallest_track["index"]} (smallest)")
   return smallest_track["index"]

def convert_to_mkv(input_file:Path, output_file:Path, audio_file:Path, delay:float, subtitle:int|Path) -> bool:
    """Run mkvmerge to create mkv with selected subtitle and all video/audio."""
    
    cmd = [
        "mkvmerge",
        "-o", str(output_file)]
    
    subtitle_index = subtitle if isinstance(subtitle, int) else 0

    # Add subtitles
    subtitle_part = ["--subtitle-tracks",
                    str(subtitle_index),
                    "--track-name",
                    f"{subtitle_index}:German (Forced)",
                    "--language", f"{subtitle_index}:de",
                    "--forced-track", f"{subtitle_index}:yes",
                    "--default-track", f"{subtitle_index}:yes",
                    "--track-enabled-flag", f"{subtitle_index}:yes"
                ]
    if isinstance(subtitle, int): 
        cmd.extend(subtitle_part)

    # Add audio file
    if audio_file:
        cmd.extend(["--no-audio", str(input_file)])
        if delay:
            cmd.extend(["-y", f"1:{int(delay*1000)}"])
        cmd.extend(["--no-video", str(audio_file)])
    else:
        cmd.extend([str(input_file)])
    
    if isinstance(subtitle, Path):
        cmd.extend(subtitle_part)
        cmd.extend([str(subtitle)])

    print("Running command:", ' '.join(cmd))
    result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print("Error running mkvmerge:", result.stderr)
        return None
    else:
        print(f"Successfully created {output_file}")
        return True

def convert_video(infile:Path, outdir:Path, audio_file:Path=None, delay:float=0.0, subtitle_file:Path=None, no_subtitles:bool=False, delete_input:bool=False):
    """Converts a movie file to a given output format using mkvmerge."""

    print(f"Processing {infile}")
    if not infile.is_file():
        print("Input file does not exist.")
        return None

    if not outdir:
        outdir = infile.parent
    output_file = outdir / (infile.stem + (' - merged' if (infile.suffix == ".mkv") else '') + '.mkv')

    # Check if audio file exists
    if audio_file:
        if not audio_file.is_file():
            print("Track file does not exist.")
            return None
        
    if no_subtitles and subtitle_file:
        print("Cannot use --no-subtitles and --subtitle-file at the same time.")
        return None
    
    if delay and not audio_file:
        print("Cannot use --delay without --audio-file.")
        return None

    # check if subtitle file exists
    if no_subtitles:
        subtitle = None
    elif subtitle_file:
        if not subtitle_file.is_file():
            print("Subtitle file does not exist.")
            return None
        subtitle = subtitle_file
    else:
        # Step 1: Select smallest subtitle stream
        subtitle = get_smallest_subtitle_track(infile)

    # Step 2: Create MKV with selected subtitle stream
    success = convert_to_mkv(input_file=infile, output_file=output_file, audio_file=audio_file, delay=delay, subtitle=subtitle)
    if success and delete_input:
        print(f"Removing {infile}")
        infile.unlink()
        if infile.suffix == ".mkv":
            output_file.rename(outdir / f"{infile.stem}.mkv")
        if audio_file:
            print(f"Removing {audio_file}")
            audio_file.unlink()
        if subtitle_file:
            print(f"Removing {subtitle_file}")
            subtitle_file.unlink()