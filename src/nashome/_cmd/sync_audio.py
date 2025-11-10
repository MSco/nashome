#!/usr/bin/env python3
"""
Sync external audio from a matching MKV file into a given MP4 video based on an episode key pattern.

You must now provide the series name explicitly via --series-name. Unless you specify a custom --pattern,
the pattern is constructed as:
    <escaped-series-name> - s\d{2}e\d{3}

Note: Curly braces in the template are escaped internally (s\d{{2}}e\d{{3}}) so Python's str.format does not
interpret them as replacement fields. The effective regex contains single braces.

Provide --pattern to override the constructed default entirely.

Usage:
    sync-audio.py <input.mp4> <input-directory> <output-directory> <series-name> [--offset OFFSET] [--pattern REGEX] [--dry-run]

Example:
    sync-audio.py "Pokemon - s01e012 Opening.mp4" ./input_dir ./out_dir Pokemon --offset -1

This will:
1. Extract an episode key from the input MP4 filename using the regex pattern.
2. Search the input-directory recursively for the first .mkv file whose name contains that episode key.
3. Produce an output MP4 in the output-directory with the same basename as the input MP4.
4. Run ffmpeg:
       ffmpeg -itsoffset <offset> -i <input.mp4> -i <input2.mkv> -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest <output.mp4>

Exit codes:
 2 - input MP4 missing
 3 - pattern not found or MKV missing
 4 - cannot create output directory
 5 - ffmpeg failed

Use --dry-run to only display the ffmpeg command.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, List

# Template (series name will be escaped and interpolated); do not include the series itself here.
# NOTE: Double braces around quantifiers so str.format does not treat them as fields.
EPISODE_PATTERN_TEMPLATE = r"{series} - s\d{{2}}e\d{{3}}"  # raw regex template -> becomes e.g. "Pokemon - s\d{2}e\d{3}"

class SyncAudioError(Exception):
    pass

def find_pattern_in_filename(filename: str, pattern: str) -> str:
    match = re.search(pattern, filename)
    if not match:
        raise SyncAudioError(f"Pattern '{pattern}' not found in filename: {filename}")
    return match.group(0)


def find_matching_mkv(input_dir: Path, episode_key: str) -> Path:
    if not input_dir.is_dir():
        raise SyncAudioError(f"Input directory does not exist or is not a directory: {input_dir}")
    candidates: List[Path] = []
    for root, _dirs, files in os.walk(input_dir):
        for f in files:
            if f.lower().endswith('.mkv') and episode_key in f:
                candidates.append(Path(root) / f)
    if not candidates:
        raise SyncAudioError(f"No matching .mkv file containing '{episode_key}' found in {input_dir}")
    return sorted(candidates)[0]


def build_ffmpeg_command(offset: int, input_mp4: Path, input_mkv: Path, output_mp4: Path) -> List[str]:
    return [
        'ffmpeg',
        '-itsoffset', str(offset),
        '-i', str(input_mp4),
        '-i', str(input_mkv),
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        str(output_mp4)
    ]


def run_ffmpeg(cmd: List[str]) -> None:
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except FileNotFoundError:
        raise SyncAudioError("ffmpeg not found in PATH. Please install ffmpeg.")
    if process.returncode != 0:
        raise SyncAudioError(f"ffmpeg failed (exit {process.returncode}). Output:\n{process.stdout}")
    print(process.stdout)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sync external audio from matching MKV into MP4 using an episode pattern.")
    p.add_argument('input_mp4', help='Path to input .mp4 file.')
    p.add_argument('input_directory', help='Directory to search for matching .mkv file.')
    p.add_argument('series_name', help='Name of the series (used to build default pattern).')
    p.add_argument('output_directory', help='Directory where output .mp4 will be written.')
    p.add_argument('--offset', type=int, default=-1, help='Audio offset passed to ffmpeg -itsoffset (default: -1).')
    p.add_argument('--pattern', default=None, help='Override regex pattern to extract key from input filename (otherwise built from series_name).')
    p.add_argument('--dry-run', action='store_true', help='Show ffmpeg command without executing.')
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    input_mp4 = Path(args.input_mp4).expanduser().resolve()
    if not input_mp4.is_file():
        print(f"ERROR: Input mp4 file not found: {input_mp4}", file=sys.stderr)
        return 2

    # Build pattern if not overridden.
    if args.pattern:
        pattern = args.pattern
    else:
        escaped_series = re.escape(args.series_name)
        pattern = EPISODE_PATTERN_TEMPLATE.format(series=escaped_series)
    print(f"Using episode pattern: {pattern}")

    try:
        episode_key = find_pattern_in_filename(input_mp4.name, pattern)
        print(f"Found episode key: {episode_key}")
        input_mkv = find_matching_mkv(Path(args.input_directory).expanduser().resolve(), episode_key)
        print(f"Using matching mkv: {input_mkv}")
    except SyncAudioError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3

    output_dir = Path(args.output_directory).expanduser().resolve()
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"ERROR: Cannot create output directory {output_dir}: {e}", file=sys.stderr)
        return 4

    output_mp4 = output_dir / input_mp4.name
    if output_mp4.exists():
        print(f"WARNING: Output file already exists and will be overwritten: {output_mp4}")

    cmd = build_ffmpeg_command(args.offset, input_mp4, input_mkv, output_mp4)
    print("FFmpeg command:")
    print(' '.join(cmd))

    if args.dry_run:
        print("Dry run: not executing ffmpeg.")
        return 0

    try:
        run_ffmpeg(cmd)
    except SyncAudioError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 5

    print(f"Success: Created {output_mp4}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
