#!/usr/bin/env python3
import argparse
import subprocess
import os
import sys
import json
import re


def run_cmd(cmd):
    """Runs a shell command and returns stdout as text."""
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print("Fehler beim Ausführen:", " ".join(cmd))
        print(result.stderr)
        sys.exit(1)
    return result.stdout


def derive_output_names(input_file):
    """
    Extracts parts from filename according to given pattern and splits group(4)
    at the middle ' _ ' (space-underscore-space) to produce split_1 and split_2.
    """

    filename = os.path.basename(input_file)

    pattern = re.compile(r'(.*) - s(\d+)e(\d+) - (.*)\.mkv')
    match = pattern.match(filename)
    if not match:
        raise ValueError("Dateiname entspricht nicht dem erwarteten Format:\n"
                         "(.*) - s(\\d+)e(\\d+) - (.*).mkv")

    part4 = match.group(4)

    # Positionen von " _ " finden
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
        # kein ' _ ' → keine echte Trennung
        split_1 = part4
        split_2 = ""
    elif len(positions) == 1:
        pos = positions[0]
        split_1 = part4[:pos]
        split_2 = part4[pos + len(sep):]
    else:
        # mittlere Position auswählen
        mid = len(positions) // 2
        pos = positions[mid]
        split_1 = part4[:pos]
        split_2 = part4[pos + len(sep):]

    # TRIMMEN
    split_1 = split_1.strip()
    split_2 = split_2.strip()

    g1, g2, g3 = match.group(1), match.group(2), match.group(3)

    # NEUE Ausgabe
    out1 = f"{g1} - s{g2}e{g3}a - {split_1}.mkv"
    out2 = f"{g1} - s{g2}e{g3}b - {split_2}.mkv"

    return out1, out2



from tqdm import tqdm
import subprocess
import json
import time

def find_black_frame(input_file, offset_seconds, window_seconds=None):
    """
    Find first black frame after offset using ffprobe blackdetect filter.
    Shows a tqdm progress bar while searching (limited update rate).
    """

    if window_seconds is not None:
        end_time = offset_seconds + window_seconds
        select_filter = f"between(t\\,{offset_seconds}\\,{end_time})"
        total_seconds_to_search = window_seconds
    else:
        select_filter = f"gte(t\\,{offset_seconds})"
        # sinnvolle Default-Balkenlänge
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

    # tqdm: wenige Updates → effizient
    with tqdm(
        total=total_seconds_to_search,
        desc="Suche nach Black Frame",
        unit="s",
        mininterval=0.5   # >=0.5s zwischen Render-Updates
    ) as pbar:

        while True:
            try:
                # Warten, aber ohne busy-waiting; ffprobe läuft ungestört weiter.
                process.wait(timeout=0.5)
                break  # Prozess ist fertig
            except subprocess.TimeoutExpired:
                # ffprobe läuft noch → Fortschritt aktualisieren
                elapsed = time.time() - start_time
                pbar.n = min(elapsed, total_seconds_to_search)
                pbar.refresh()

        # Prozess beendet → Balken voll machen
        pbar.n = total_seconds_to_search
        pbar.refresh()

    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print("Fehler beim ffprobe-Aufruf:")
        print(stderr)
        sys.exit(1)

    data = json.loads(stdout or "{}")
    frames = data.get("frames", [])

    for frame in frames:
        tags = frame.get("tags", {})
        if "lavfi.black_start" in tags:
            return float(tags["lavfi.black_start"])

    return None

def split_video(input_file, output_dir, split_time, out1_name, out2_name):
    """
    Splits input video into two parts at split_time (seconds).
    """

    part1 = os.path.join(output_dir, out1_name)
    part2 = os.path.join(output_dir, out2_name)

    print(f"➡️  Erstelle: {part1}")
    cmd1 = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-to", str(split_time),
        "-c", "copy",
        part1
    ]
    run_cmd(cmd1)

    print(f"➡️  Erstelle: {part2}")
    cmd2 = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-ss", str(split_time),
        "-c", "copy",
        part2
    ]
    run_cmd(cmd2)

    print("✔️  Split erfolgreich abgeschlossen.")


def main():
    parser = argparse.ArgumentParser(description="Split MKV video at first black frame after offset.")
    parser.add_argument("input", help="Eingabe-MKV-Datei")
    parser.add_argument("output_dir", help="Ausgabeverzeichnis")
    parser.add_argument("--offset", type=float, default=0, help="Offset in Minuten")
    parser.add_argument("--search-window", type=float, default=None,
                        help="Maximales Suchfenster ab Offset in Minuten")

    args = parser.parse_args()

    input_file = args.input
    output_dir = args.output_dir
    offset_seconds = args.offset * 60
    window_seconds = args.search_window * 60 if args.search_window else None

    if not os.path.isfile(input_file):
        print("❌ Fehler: Eingabedatei existiert nicht.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    print("🔍 Berechne Ausgabedateinamen…")
    try:
        out1_name, out2_name = derive_output_names(input_file)
    except ValueError as e:
        print("❌", e)
        sys.exit(1)

    print("🔍 Suche nach Black Frame…")
    black_time = find_black_frame(input_file, offset_seconds, window_seconds)

    if black_time is None:
        print("⚠️ Kein Black Frame im angegebenen Bereich gefunden.")
        # Gesamtes Video einfach kopieren
        import shutil
        out1_name, _ = derive_output_names(input_file)
        out_path = os.path.join(output_dir, out1_name)
        shutil.copy2(input_file, out_path)
        print(f"📄 Gesamtes Video wurde nach '{out_path}' kopiert.")
        sys.exit(0)


    print(f"✔️ Black Frame gefunden bei {black_time:.2f} Sekunden.")

    split_video(input_file, output_dir, black_time, out1_name, out2_name)


if __name__ == "__main__":
    main()
