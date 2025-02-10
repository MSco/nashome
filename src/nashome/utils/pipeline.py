from pathlib import Path
import shutil

from nashome.utils.renamer import cleanup_recordings
from nashome.utils.movie import cut_video, check_template_root_directory

def cleanup_and_autocut(recordings_root_path:Path, template_root_directory:Path, outdir_root_path:Path, offset:float=0, movie_length_minutes:float=None):
    # Check if the directories exist
    if not recordings_root_path.is_dir():
        print("Error: The recordings root path does not exist.")
        return False
    if not template_root_directory.is_dir():
        print("Error: The template directory does not exist.")
        return False
    if not outdir_root_path.is_dir():
        outdir_root_path.mkdir(parents=True)

    for recording_directory in recordings_root_path.iterdir():
        if not recording_directory.is_dir():
            continue

        template_name = recording_directory.name.lower().replace(" ", "_")
        template_directory = template_root_directory / template_name

        start_template_images, end_template_images = check_template_root_directory(template_directory)
        if not start_template_images or not end_template_images:
            print(f"Error: Could not find start or end template directory for {template_name}.")
            continue

        # Get all the recordings in the directory
        recording_movie_files = [f for f in recording_directory.iterdir() if f.is_file() and f.name.endswith(".ts")]
        if not recording_movie_files:
            print(f"No recordings found in {recording_directory.name}.")
            continue

        # Create the output directory
        outdir = outdir_root_path/recording_directory.name
        if not outdir.is_dir():
            outdir.mkdir()

        # Create a temporary output directory
        temporary_indir = outdir_root_path / f"_autocut_{template_name}"
        if not temporary_indir.is_dir():
            temporary_indir.mkdir()

        for recording_movie_file in recording_movie_files:
            # copy the recordings to the temporary directory   
            for file in [f for f in recording_directory.iterdir() if f.name.startswith(recording_movie_file.stem)]:
                if not file.is_file():
                    continue
                print(f"Copying {file} to {temporary_indir/file.name}")
                shutil.copy(file, temporary_indir/file.name)

            recording_files = [f for f in temporary_indir.iterdir() if f.is_file()]
            if not recording_files:
                print(f"Error: No recordings found in {temporary_indir.name}.")
                continue

            # Cleanup the recordings
            cleanup_recordings(paths=recording_files, series=True, dash=False, force_tmdb=True, force_rename=True)

            movie_file = [f for f in temporary_indir.iterdir() if f.is_file() and f.name.endswith(".ts")][0]
            temporary_outdir = temporary_indir / "trimmed"

            # Autocut the recordings
            cut_video(video_path=movie_file, 
                    template_dir=template_directory,
                    outdir=temporary_outdir,
                    offset_minutes=offset,
                    movie_length_minutes=movie_length_minutes)

            # move the files to the output directory        
            for file in list(temporary_outdir.iterdir()) + [f for f in temporary_indir.iterdir() if f.name.endswith((".eit", ".meta"))]:
                print(f"Moving {file} to {outdir/file.name}")
                file.rename(outdir/file.name)

            # delete copy of input movie file
            movie_file.unlink()

        # cleanup the temporary directory
        print(f"Removing {temporary_indir}")
        shutil.rmtree(temporary_indir)    