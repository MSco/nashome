'''
Liest aus Dateien mit den Mustern

Screenshot_YYMMDD_HHMMSS_...jpg
IMG_YYMMDD_WAXXX.jpg

Das Datum und gegebenenfalls die Uhrzeit heraus.
'''
from pathlib import Path
import subprocess

from nashome.photos.photo import Photo

# path = '/volume1/photo/'
# path = '/localdata/src/python/nashome/photos'
def fix_photos(path:str|Path, dry_run:bool, force:bool, gps_coordinates:str|None, synology:bool):
    for root, dirnames, filenames in Path(path).walk():
        if "@" in str(root):
            continue
        for old_filename in sorted(filenames):
            old_path = root/old_filename
            
            # Liest das Datum und die Uhrzeit aus dem Dateinamen
            photo = Photo(old_path)
            rename = photo.new_filename != old_filename
            if not rename and not force:
                print(f"Skipping {old_filename} ...")
                continue

            if photo.date is not None:
                photo.update_exif_datetime(dry_run=dry_run)
            else:
                print(f"No date found in filename {old_filename}")

            if photo.new_filename is None:
                continue

            # Benennt die Dateien um
            new_path = root/photo.new_filename
            if new_path.exists():
                print(f"File {new_path} already exists")
                continue
            
            if rename:
                print(f"{'[DRY RUN] ' if dry_run else ''}Rename {old_path.name} to {new_path.name}")
                if not dry_run:
                    old_path.rename(new_path)
            
                # Füge neue Dateienamen in den Index ein und lösche die alten aus dem Index
                if synology and not dry_run:
                    subprocess.call(["synoindex", "-n", new_path, old_path])
            
            print('Done!\n')
