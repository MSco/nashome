#!/usr/bin/env python
import argparse
from pathlib import Path

from nashome.savegames.savegame_handler import sync_savegames

def main():
    # argument parsing
    parser = argparse.ArgumentParser(description="Synchronize savegames from source directory to destination directory", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('source', type=Path, help="Path to the source directory (JKSV-root)")
    parser.add_argument('destination', type=Path, help="Path to the destination directory (JKSV-root)")
    args = parser.parse_args()

    sync_savegames(source_root_dir=args.source, dest_root_dir=args.destination)

if __name__ == "__main__":
    main()
