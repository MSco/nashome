#!/usr/bin/env python
import argparse
from pathlib import Path

from nashome.photos.photo_handler import fix_photos

def main():
    # argument parsing
    parser = argparse.ArgumentParser(description="Rename photos and add datetime meta information.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('inpath', type=Path, help="Path to the input directory.")
    parser.add_argument('-d', '--disable-synology', action='store_true', help="Disable Synology specific features.")
    args = parser.parse_args()

    fix_photos(path=args.inpath, disable_synology=args.disable_synology)

if __name__ == "__main__":
    main()
