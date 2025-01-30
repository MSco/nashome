#!/usr/bin/env python
import argparse
from pathlib import Path

from nashome.youtube.downloader import download_youtube

def main():
    # argument parsing
    parser = argparse.ArgumentParser(description="Download movie(s) from YouTube movie/playlist url.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('urls', type=str, nargs='+', help="YouTube movie/playlist url(s).")
    parser.add_argument('outdir', type=Path, help="Path to the output directory.")
    parser.add_argument('-a', "--audio-only", action='store_true', help="If specified, only the audio stream will be downloaded and converted to mp3.")
    parser.add_argument('-l', "--language", type=str, help="If specified, the video will be re-dubbed with an extra audio stream in given language, if available (default: German).")
    
    args = parser.parse_args()

    download_youtube(urls=args.urls, outdir=args.outdir, audio_only=args.audio_only, language=args.language)

if __name__ == "__main__":
    main()
