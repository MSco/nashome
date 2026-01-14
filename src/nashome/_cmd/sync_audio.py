#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path


def timestamp_to_seconds(ts):
    # Convert HH:MM:SS.mmm to seconds as float
    hours, minutes, seconds = ts.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def run_command(cmd):
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Create a new video consisting of two parts with delayed audio in the second part."
    )
    parser.add_argument("input", help="Input video file")
    parser.add_argument("timestamp1", help="End of first part (HH:MM:SS.mmm)")
    parser.add_argument("timestamp2", help="Start of second part (HH:MM:SS.mmm)")
    parser.add_argument("outdir", help="Output directory")

    args = parser.parse_args()

    input_file = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    delayed_file = outdir / "delayed.mp4"

    # Keep original filename for output
    output_file = outdir / input_file.name

    t1 = timestamp_to_seconds(args.timestamp1)
    t2 = timestamp_to_seconds(args.timestamp2)

    if t2 <= t1:
        raise ValueError("timestamp2 must be greater than timestamp1")

    # Audio delay in seconds
    audio_delay_seconds = t2 - t1
    print(f"Audio will be delayed by {audio_delay_seconds} seconds in the second part.")

    # Part 2: from timestamp2 to end, audio delayed
    run_command([
        "ffmpeg",
        "-i", str(input_file),
        "-itsoffset", str(audio_delay_seconds),
        "-i", str(input_file),
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(delayed_file)
    ])


    run_command([
        "ffmpeg",
        "-i", str(input_file),
        "-i", str(delayed_file),
        "-filter_complex",
        f"[0:v]trim=0:{t1},setpts=PTS-STARTPTS[v0];"
        f"[0:a]atrim=0:{t1},asetpts=PTS-STARTPTS[a0];"
        f"[1:v]trim={t2},setpts=PTS-STARTPTS[v1];"
        f"[1:a]atrim={t2},asetpts=PTS-STARTPTS[a1];"
        f"[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]",
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libsvtav1",
        "-crf", "28",
        "-b:v", "0",
        "-c:a", "aac",
        "-b:a", "128k",
        str(output_file)    
    ])

    print("Done.")
    print("Output file:", output_file)


if __name__ == "__main__":
    main()
