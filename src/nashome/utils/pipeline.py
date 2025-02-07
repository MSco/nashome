from pathlib import Path
import shutil
import subprocess

from nashome.utils.constants import TEMPLATE_START_TEMPLATE, TEMPLATE_END_TEMPLATE
from nashome.utils.renamer import cleanup_recordings
from nashome.utils.movie import cut_video

def cleanup_and_autocut(recordings_root_path:Path, template_directory:Path, outdir_root_path:Path):
    # Check if the directories exist
    if not recordings_root_path.is_dir():
        print("Error: The recordings root path does not exist.")
        return False
    if not template_directory.is_dir():
        print("Error: The template directory does not exist.")
        return False
    if not outdir_root_path.is_dir():
        outdir_root_path.mkdir(parents=True)

    for recording_directory in recordings_root_path.iterdir():
        if not recording_directory.is_dir():
            continue

        template_name = recording_directory.name.lower().replace(" ", "_")
        start_template_path = template_directory / TEMPLATE_START_TEMPLATE.replace("<D>", template_name)
        end_template_path = template_directory / TEMPLATE_END_TEMPLATE.replace("<D>", template_name)

        if not start_template_path.is_file() or not end_template_path.is_file():
            print(f"Error: Could not find templates for {recording_directory.name}.")
            continue

        # Get all the recordings in the directory
        recording_files = [f for f in recording_directory.iterdir() if f.is_file()]
        if not recording_files:
            print(f"Error: No recordings found in {recording_directory.name}.")
            continue

        # Create a temporary output directory
        temporary_indir = outdir_root_path / f"_autocut_{template_name}"
        rsync_cmd = ["rsync", "-avP", str(recording_directory)+'/', str(temporary_indir)+'/']
        result = subprocess.run(rsync_cmd)

        if not result.returncode == 0:
            print(f"Error: rsync command failed: {" ".join(rsync_cmd)}")
            continue

        recording_files = [f for f in temporary_indir.iterdir() if f.is_file()]
        if not recording_files:
            print(f"Error: No recordings found in {temporary_indir.name}.")
            continue

        # Cleanup the recordings
        cleanup_recordings(paths=recording_files, series=True, dash=False, force_tmdb=True, force_rename=True)

        movie_file = temporary_indir.glob("*.ts")
        temporary_outdir = temporary_indir / "trimmed"

        # Autocut the recordings
        cut_video(video_path=movie_file, 
                  start_template_path=start_template_path, 
                  end_template_path=end_template_path, 
                  outdir=temporary_outdir,
                  offset_minutes=5,
                  movie_length_minutes=18)

        # cleanup the temporary directory
        shutil.rmtree(temporary_indir)    