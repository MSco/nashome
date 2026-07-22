#!/usr/bin/env python
import argparse
from pathlib import Path

from nashome.photos.photo_handler import fix_photos

def main():
    # argument parsing
    parser = argparse.ArgumentParser(description="Rename photos and add datetime meta information.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('inpath', type=Path, help="Path to the input directory.")
    parser.add_argument('-d', '--dry-run', action='store_true', help="Perform a dry run without making any changes.")
    parser.add_argument('-f', '--force', action='store_true', help="Force overwrite existing tags.")
    parser.add_argument('-g', '-gps', '--gps-coordinates', type=str, help="Add GPS coordinates in DMS format (e.g. '48 deg 51' 29.99\" N, 2 deg 17' 40.99\" E) or in decimal format (e.g. '48.8583, 2.2945'). Altitude can also be added (e.g. '48.8583, 2.2945, 100').")
    parser.add_argument('-s', '--synology', action='store_true', help="Update Synology index.")
    args = parser.parse_args()

    fix_photos(path=args.inpath, dry_run=args.dry_run, force=args.force, gps_coordinates=args.gps_coordinates, synology=args.synology)

if __name__ == "__main__":
    main()
