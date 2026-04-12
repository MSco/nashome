'''
Liest aus Dateien mit den Mustern

Screenshot_YYMMDD_HHMMSS_...jpg
IMG_YYMMDD_WAXXX.jpg

Das Datum und gegebenenfalls die Uhrzeit heraus.
'''
from datetime import datetime
from pathlib import Path
import re
import subprocess

from nashome.photos.img_filename_pattern import ImageFilenamePattern

def extract_datetime_from_filename(filename:str) -> tuple[datetime,str]:
    patterns = [
        ImageFilenamePattern(r'Screenshot_(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})(.*)\.jpe?g',  True), # Screenshot_YYYY-MM-DD-HH-MM-SS_<hashcode>.jpg
        ImageFilenamePattern(r'IMG[-_](\d{4})(\d{2})(\d{2})([-_]WA\d+.*)\.jpe?g', True),  # IMG-YYYYMMDD-WAXXXX.jpg
        ImageFilenamePattern(r'IMG[-_]?(\d{4})(\d{2})(\d{2})[-_]?(\d{2})(\d{2})(\d{2})(.*)\.jpe?g',  True), # IMG(-_)YYYYMMDD(-_)HHMMSS.jpg
        ImageFilenamePattern(r'(\d{4})(\d{2})(\d{2})[-_](\d{2})(\d{2})(\d{2})(.*)\.jpe?g', True)  # YYYYMMDD_HHMMSS.jpg
    ]

    for pattern in patterns:
        match_filename = re.match(pattern.pattern, filename)
        if match_filename is not None:
            groups = match_filename.groups()
            date_str = "".join(groups[:3])
            if len(groups)>=6:
                time_str = "".join(groups[3:6])
                date = datetime.strptime(date_str + time_str, '%Y%m%d%H%M%S') if pattern.change_exif else None
                base_str = f"{date_str}_{time_str}"
            else:
                date = datetime.strptime(date_str, '%Y%m%d') if pattern.change_exif else None
                base_str = date_str
            return date, f"IMG_{base_str}{groups[-1]}.jpg"
        
    return None, None

def insert_exif_datetime(path: str|Path, date: datetime):
    datetime_str = date.strftime("%Y:%m:%d %H:%M:%S")
    print(f"Writing EXIF DateTimeOriginal={datetime_str} to {path}")

    subprocess.run([
        "exiftool",
        "-overwrite_original",
        f"-DateTimeOriginal={datetime_str}",
        f"-CreateDate={datetime_str}",
        f"-ModifyDate={datetime_str}",
        str(path),
    ])

# path = '/volume1/photo/'
# path = '/localdata/src/python/nashome/photos'
def fix_photos(path:str|Path, disable_synology:bool):    
    for root, dirnames, filenames in Path(path).walk():
        if "@" in str(root):
            continue
        for old_filename in sorted(filenames):
            old_path = root/old_filename
            
            # Liest das Datum und die Uhrzeit aus dem Dateinamen
            date, new_filename = extract_datetime_from_filename(old_filename)
            
            if date is not None:
                insert_exif_datetime(old_path, date)
            else:
                print(f"No date found in filename {old_filename}")

            if new_filename is None:
                continue

            # Benennt die Dateien um
            new_path = root/new_filename
            if new_path.exists():
                print(f"File {new_path} already exists")
                continue
            
            print(f"Rename {old_path.name} to {new_path.name}")
            old_path.rename(new_path)
            
            # Füge neue Dateienamen in den Index ein und lösche die alten aus dem Index
            if not disable_synology:
                subprocess.call(["synoindex", "-d", old_path])
                subprocess.call(["synoindex", "-a", new_path])
            
            print('Done!\n')      
