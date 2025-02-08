#!/usr/bin/env python
import argparse
from pathlib import Path

from nashome.utils.movie import cut_video

def main():
    # argument parsing
    parser = argparse.ArgumentParser(description="Cut movie by given start and end templates", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('movie', type=Path, help="Path to the movie file.")
    parser.add_argument('template', metavar="template-dir", type=Path, help="Path to the template image files.")
    parser.add_argument('outdir', type=Path, help="Path to the output directory.")
    parser.add_argument('-o', "--offset", type=float, default=0, help="Set the start offset of the movie in minutes.")
    parser.add_argument('-l', "--length", type=float, help="Set the length of the movie in minutes.")
    
    args = parser.parse_args()

    cut_video(video_path=args.movie, 
              template_dir=args.template, 
              outdir=args.outdir, 
              offset_minutes=args.offset, 
              movie_length_minutes=args.length)

if __name__ == "__main__":
    main()
