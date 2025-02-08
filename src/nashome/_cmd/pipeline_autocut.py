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
    
    args = parser.parse_args()

    cleanup_and_autocut(recordings_root_path=args.recordings, 
                        template_root_directory=args.template, 
                        outdir_root_path=args.outdir)

if __name__ == "__main__":
    main()
