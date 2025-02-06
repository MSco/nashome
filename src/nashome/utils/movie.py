import cv2
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

def find_template(frame:cv2.typing.MatLike, template:cv2.typing.MatLike, threshold:float=0.8) -> bool:
    """
    Searches for the template in the given frame.
    Returns True if the template is found with a confidence above the threshold.
    """
    result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_val >= threshold

def cut_video(video_path:str|Path, start_template_path:str|Path, end_template_path:str|Path, outdir:str|Path, offset_minutes:int, movie_length_minutes:int) -> bool:
    # Load the template images in grayscale
    start_template = cv2.imread(start_template_path, cv2.IMREAD_GRAYSCALE)
    end_template = cv2.imread(end_template_path, cv2.IMREAD_GRAYSCALE)

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
    frame_index = offset_minutes * 60 * fps
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert the frame to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Check for the start template
        if start_frame_index is None and find_template(gray_frame, start_template):
            start_frame_index = frame_index
            print(f"Start template found at frame {start_frame_index}")
            if movie_length_minutes:
                frame_index += 60 * fps * (movie_length_minutes)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

        # Check for the end template
        elif start_frame_index is not None and end_frame_index is None:
            if find_template(gray_frame, end_template):
                end_frame_index = frame_index
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