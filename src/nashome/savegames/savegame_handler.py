from pathlib import Path


def sync_savegames(source_root_dir: str|Path, dest_root_dir: str|Path) -> None:
    """
    Synchronizes save game files from a source directory to a destination directory.
    This function iterates over game directories in the source root directory, finds the latest
    date directory within each game directory, and copies the files from the latest date directory
    in the source to the corresponding latest date directory in the destination.
    Args:
        source_root_dir (str | Path): The root directory containing the source game directories.
        dest_root_dir (str | Path): The root directory containing the destination game directories.
    Raises:
        FileNotFoundError: If the source or destination root directory does not exist.
    """
    source_root_dir = Path(source_root_dir)
    dest_root_dir = Path(dest_root_dir)

    if not source_root_dir.is_dir():
        raise FileNotFoundError(f"Source directory '{source_root_dir}' not found.")
    
    if not dest_root_dir.is_dir():
        raise FileNotFoundError(f"Destination directory '{dest_root_dir}' not found.")
    
    # Iterate over the source game directories
    for source_game_dir in source_root_dir.iterdir():
        dest_game_dir = dest_root_dir / source_game_dir.name
        if not dest_game_dir.exists():
            print(f"'{dest_game_dir}' not found. Skipping.")
            continue
        
        # Get the latest date directory
        source_date_dir = sorted(source_game_dir.iterdir())[-1]
        dest_date_dir = sorted(dest_game_dir.iterdir())[-1]

        # Check if the directories are valid
        if not source_date_dir.is_dir():
            print(f"'{source_date_dir}' is not a directory. Skipping.")
            continue

        # Check if the directories are valid
        if not dest_date_dir.is_dir():
            print(f"'{dest_date_dir}' is not a directory. Skipping.")
            continue

        # Copy the files
        for source_file in source_date_dir.iterdir():
            dest_file = dest_date_dir / source_file.name
            
            print(f"Copying '{source_file}' to '{dest_file}'")
            dest_file.write_bytes(source_file.read_bytes())
