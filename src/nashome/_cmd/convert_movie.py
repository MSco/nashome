#!/usr/bin/env python
import argparse
from pathlib import Path

from nashome.utils.movie import convert_video

def main():
    # argument parsing
    parser = argparse.ArgumentParser(description="Converts a movie file to a given output format using ffmpeg", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('infile', type=Path, help="Path to the input video file")
    parser.add_argument('-o', '--outdir', type=Path, help="Path to output directory (default: same as input file)")
    args = parser.parse_args()

    convert_video(infile=args.infile, outdir=args.outdir)

if __name__ == "__main__":
    main()
