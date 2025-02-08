#!/usr/bin/env python
import argparse
from pathlib import Path

from nashome.utils.pipeline import cleanup_and_autocut

def main():
    # argument parsing
    parser = argparse.ArgumentParser(description="Copy recordings, rename them and autocut", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('recordings', metavar="recordings-root-directory", type=Path, help="Path to the recordings autocut input directory.")
    parser.add_argument('template', metavar="template-directory", type=Path, help="Path to the template image file directory.")
    parser.add_argument('outdir', metavar="outdir-root-directory", type=Path, help="Path to the series output root directory.")
    parser.add_argument('-o', "--offset", type=float, default=0, help="Set the start offset of the movie in minutes.")
    parser.add_argument('-l', "--length", type=float, help="Set the length of the movie in minutes.")
    
    args = parser.parse_args()

    cleanup_and_autocut(recordings_root_path=args.recordings, 
                        template_root_directory=args.template, 
                        outdir_root_path=args.outdir,
                        offset=args.offset,
                        movie_length_minutes=args.length)

if __name__ == "__main__":
    main()
