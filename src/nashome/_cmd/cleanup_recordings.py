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
    parser.add_argument('-t', '-tmdb', "--force-tmdb", action='store_true', help="Set this flag to force tmdb search for series.")
    parser.add_argument('-f', "--force-rename", action='store_true', help="Set this flag to force renaming files without prompt.")
    parser.add_argument('-d', "--dash", type=str, help="Set this flag if the series/movie name contains a dash.")
    parser.add_argument('-n', '-nt', "--no-tmdb", action='store_true', help="Set this flag to rename files without using tmdb or eit content.")
    parser.add_argument('-l', "--language", type=str, default="de-DE", help="Set this flag to change language code (default: de-DE).")
    parser.add_argument('-ta', "--try-all-seasons", action='store_true', help="If specified, season id will not be read from title. All season ids will be tried.")
    
    args = parser.parse_args()

    cleanup_recordings(paths=args.files, series=args.series, force_tmdb=args.force_tmdb, force_rename=args.force_rename, dash=args.dash, no_tmdb=args.no_tmdb, language_code=args.language, try_all_seasons=args.try_all_seasons)

if __name__ == "__main__":
    main()
