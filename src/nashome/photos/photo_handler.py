'''
Liest aus Dateien mit den Mustern

Screenshot_YYMMDD_HHMMSS_...jpg
IMG_YYMMDD_WAXXX.jpg

Das Datum und gegebenenfalls die Uhrzeit heraus.
'''
from datetime import datetime
from pathlib import Path
import piexif
import re
import subprocess

def extract_datetime_from_filename(filename:str) -> tuple[datetime,str]:
    patterns = [
        r'IMG(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(.*)\.jpe?g',  # IMGYYYYMMDDHHMMSS.jpg
        r'Screenshot_(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})(.*)\.jpe?g',  # Screenshot_YYYY-MM-DD-HH-MM-SS_<hashcode>.jpg
        r'IMG-(\d{4})(\d{2})(\d{2})(-WA\d+.*)\.jpe?g',  # IMG-YYYYMMDD-WAXXXX.jpg
        r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})(.*)\.jpe?g'  # YYYYMMDD_HHMMSS.jpg
    ]
    
    for pattern in patterns:
        match = re.match(pattern, filename)
        if match is not None:
            groups = match.groups()
            date_str = "".join(groups[:3])
            if len(groups)>=6:
                time_str = "".join(groups[3:6])
                date = datetime.strptime(date_str + time_str, '%Y%m%d%H%M%S')
                base_str = f"{date_str}_{time_str}"
            else:
                date = datetime.strptime(date_str, '%Y%m%d')
                base_str = date_str
            return date, f"IMG_{base_str}{groups[-1]}.jpg"
    return None, None


def insert_exif_datetime(image_path:str|Path, date:datetime):
    # create datetime string
    datetime_str = f"{date.year}:{date.month}:{date.day} {date.hour}:{date.minute}:{date.second}"

    # create exif data
    exif_dict = {'Exif': {
                     piexif.ExifIFD.DateTimeOriginal: datetime_str,
                     piexif.ExifIFD.DateTimeDigitized: datetime_str
                }}
    exif_bytes = piexif.dump(exif_dict)

    # insert exif data into image
    print(f"Inserting EXIF data {datetime_str} into {image_path}")
    piexif.insert(exif_bytes, str(image_path))

# path = '/volume1/photo/'
# path = '/localdata/src/python/nashome/photos'
def fix_photos(path:str|Path, disable_synology:bool):    
    for root, dirnames, filenames in Path(path).walk():
        for old_filename in filenames:
            old_path = root/old_filename
            
            # Liest das Datum und die Uhrzeit aus dem Dateinamen
            date, new_filename = extract_datetime_from_filename(old_filename)
            
            if date is None:
                continue

            # Benennt die Dateien um
            new_path = root/new_filename
            old_path.rename(new_path)
            
            # Fügt das Datum und die Uhrzeit als Meta-Daten in die Bild-Datei ein
            insert_exif_datetime(new_path, date)
            
            # Füge neue Dateienamen in den Index ein und lösche die alten aus dem Index
            if not disable_synology:
                subprocess.call(["synoindex", "-a", new_path])
                subprocess.call(["synoindex", "-d", old_path])
            
            print('Done!\n')      
