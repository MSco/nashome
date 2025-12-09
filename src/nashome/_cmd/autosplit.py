#!/usr/bin/env python3
import argparse
import subprocess
import os
import sys
import json
import re
import shutil
import time
from tqdm import tqdm

"""
Fehlender Anfang:
s06e006
s06e008
s06e022
s06e032
s06e045
"""

def run_cmd(cmd):
    """Runs a shell command and returns stdout as text."""
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print("Error while running:", " ".join(cmd))
        print(result.stderr)
        sys.exit(1)
    return result.stdout


def derive_output_names(input_file):
    """
    Extracts parts from filename, splits group(4) at the middle ' _ '.
    """

    filename = os.path.basename(input_file)
    pattern = re.compile(r'(.*) - s(\d+)e(\d+) - (.*)\.mkv')
    match = pattern.match(filename)
    if not match:
        raise ValueError("Filename does not match expected format:\n"
                         "(.*) - s(\\d+)e(\\d+) - (.*).mkv")

    part4 = match.group(4)
    sep = " _ "

    positions = []
    start = 0
    while True:
        idx = part4.find(sep, start)
        if idx == -1:
            break
        positions.append(idx)
        start = idx + len(sep)

    if len(positions) == 0:
        split_1 = part4
        split_2 = ""
    elif len(positions) == 1:
        pos = positions[0]
        split_1 = part4[:pos]
        split_2 = part4[pos + len(sep):]
    else:
        mid = len(positions) // 2
        pos = positions[mid]
        split_1 = part4[:pos]
        split_2 = part4[pos + len(sep):]

    split_1 = split_1.strip()
    split_2 = split_2.strip()

    g1, g2, g3 = match.group(1), match.group(2), match.group(3)

    out1 = f"{g1} - s{g2}e{g3}a - {split_1}.mkv"
    out2 = f"{g1} - s{g2}e{g3}b - {split_2}.mkv"

    return out1, out2


def find_black_frame(input_file, offset_seconds, window_seconds=None):
    """
    Searches for the first black frame after offset. Shows tqdm progress bar.
    """

    if window_seconds is not None:
        end_time = offset_seconds + window_seconds
        select_filter = f"between(t\\,{offset_seconds}\\,{end_time})"
        total_seconds_to_search = window_seconds
    else:
        select_filter = f"gte(t\\,{offset_seconds})"
        total_seconds_to_search = 30

    cmd = [
        "ffprobe",
        "-f", "lavfi",
        f"movie='{input_file}',select='{select_filter}',blackdetect=d=0.1:pic_th=0.98",
        "-show_entries", "frame_tags=lavfi.black_start",
        "-of", "json"
    ]

    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    start_time = time.time()

    with tqdm(
        total=total_seconds_to_search,
        desc="Searching black frame",
        unit="s",
        mininterval=0.5
    ) as pbar:

        while True:
            try:
                process.wait(timeout=0.5)
                break
            except subprocess.TimeoutExpired:
                elapsed = time.time() - start_time
                pbar.n = min(elapsed, total_seconds_to_search)
                pbar.refresh()

        pbar.n = total_seconds_to_search
        pbar.refresh()

    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print("Error running ffprobe:")
        print(stderr)
        sys.exit(1)

    data = json.loads(stdout or "{}")
    frames = data.get("frames", [])
    black_times = []

    for frame in frames:
        tags = frame.get("tags", {})
        if "lavfi.black_start" in tags:
            try:
                black_times.append(float(tags["lavfi.black_start"]))
            except ValueError:
                pass

    if not black_times:
        return None

    return min(black_times)


def split_video(input_file, output_dir, split_time, out1_name, out2_name, force_reencode_second=False):
    """
    Splits the video. If force_reencode_second=True, second part is re-encoded.
    """

    part1 = os.path.join(output_dir, out1_name)
    part2 = os.path.join(output_dir, out2_name)

    # First part always copy
    print("Creating:", part1)
    cmd1 = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-to", str(split_time),
        "-c", "copy",
        part1
    ]
    run_cmd(cmd1)

    print("Creating:", part2)

    if force_reencode_second:
        # Re-encode for clean start
        cmd2 = [
            "ffmpeg", "-y",
            "-i", input_file,
            "-ss", str(split_time),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "copy",
            part2
        ]
    else:
        cmd2 = [
            "ffmpeg", "-y",
            "-i", input_file,
            "-ss", str(split_time),
            "-c", "copy",
            part2
        ]

    run_cmd(cmd2)
    print("Split completed.")


def parse_timecode(tc):
    """
    Converts HH:MM:SS.mmm into seconds (float).
    """
    m = re.match(r"(\d+):(\d+):(\d+)\.(\d+)", tc)
    if not m:
        raise ValueError("Manual split time must be in format HH:MM:SS.mmm")
    h, m_, s, ms = m.groups()
    return int(h) * 3600 + int(m_) * 60 + int(s) + int(ms) / 1000.0


def main():
    parser = argparse.ArgumentParser(description="Split MKV video at black frame or manual timestamp.")
    parser.add_argument("input", help="Input MKV")
    parser.add_argument("output_dir", help="Output directory")
    parser.add_argument("--offset", type=float, default=0, help="Offset in minutes")
    parser.add_argument("--search-window", type=float, default=None,
                        help="Search window in minutes")
    parser.add_argument("--manual-split", type=str, default=None,
                        help='Manual split time "HH:MM:SS.mmm"')
    parser.add_argument("--reencode-second-part", action="store_true",
                        help="Force re-encoding of second part")

    args = parser.parse_args()

    input_file = args.input
    output_dir = args.output_dir
    offset_seconds = args.offset * 60
    window_seconds = args.search_window * 60 if args.search_window else None
    manual_split = args.manual_split
    force_reencode = args.reencode_second_part

    if not os.path.isfile(input_file):
        print("Input file does not exist.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    print("Generating output names...")
    out1_name, out2_name = derive_output_names(input_file)

    # Manual split
    if manual_split:
        print("Using manual split time:", manual_split)
        split_time = parse_timecode(manual_split)
        split_video(
            input_file, output_dir, split_time,
            out1_name, out2_name,
            force_reencode_second=True  # always reencode for manual split
        )
        sys.exit(0)

    print("Searching for black frame...")
    black_time = find_black_frame(input_file, offset_seconds, window_seconds)

    if black_time is None:
        print("No black frame found. Copying whole file.")
        out1_name, _ = derive_output_names(input_file)
        shutil.copy2(input_file, os.path.join(output_dir, out1_name))
        sys.exit(0)

    print("Black frame found at %.3f seconds." % black_time)

    split_video(
        input_file, output_dir, black_time,
        out1_name, out2_name,
        force_reencode_second=force_reencode
    )


if __name__ == "__main__":
    main()
