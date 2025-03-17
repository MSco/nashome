#!/usr/bin/env python
import argparse
from pathlib import Path

from nashome.utils.movie import convert_video

def main():
    # argument parsing
    parser = argparse.ArgumentParser(description="Converts a movie file to a given output format using ffmpeg", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('infile', type=Path, help="Path to the input video file")
    parser.add_argument('-o', '--outdir', type=Path, help="Path to output directory (default: same as input file)")
    parser.add_argument('-a', '--audio-file', type=Path, help="Use audio track from this file (default: use audio from input file)")
    parser.add_argument('-d', "--delay", type=float, help="Add a delay to the audio track in seconds (default: 0.0)")
    parser.add_argument('-s', '--subtitle-file', type=Path, help="Use subtitle track from this file (default: use smallest subtitle track from input file)")
    parser.add_argument('-ns', '--no-subtitles', action='store_true', help="Set this flag to disable extracting subtitles")
    parser.add_argument('-del', '--delete-input', action='store_true', help="Set this flag to delete the input file after conversion")
    args = parser.parse_args()

    convert_video(infile=args.infile, outdir=args.outdir, audio_file=args.audio_file, delay=args.delay ,subtitle_file=args.subtitle_file, no_subtitles=args.no_subtitles, delete_input=args.delete_input)

if __name__ == "__main__":
    main()
