#!/usr/bin/env python
'''
Created on 13.07.2022

@author: mschober
'''

import argparse
from pathlib import Path

from nashome.utils.renamer import cleanup_recordings

def main():
    # argument parsing
    parser = argparse.ArgumentParser(description="Rename recordings.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('files', type=Path, nargs='+', help="YouTube movie/playlist url(s).")
    parser.add_argument('-s', "--series", action='store_true', help="Set this flag to rename series.")
    parser.add_argument('-d', "--dash", type=str, help="Set this flag if the series/movie name contains a dash.")
    parser.add_argument('-t', '-tmdb', "--force-tmdb", action='store_true', help="Set this flag to force tmdb search for series.")
    parser.add_argument('-f', "--force-rename", action='store_true', help="Set this flag to force renaming files without prompt.")
    
    args = parser.parse_args()

    cleanup_recordings(paths=args.files, series=args.series, dash=args.dash, force_tmdb=args.force_tmdb, force_rename=args.force_rename)

if __name__ == "__main__":
    main()
