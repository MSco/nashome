'''
Created on 25.10.2020

@author: Puddies, synology-forum.de
@version: 1.0.0-20201029
'''

import os
from datetime import datetime
import piexif
import re
import subprocess

'''
Liest aus Dateien mit den Mustern

Screenshot_YYMMDD_HHMMSS_...jpg
IMG_YYMMDD_WAXXX.jpg

Das Datum und gegebenenfalls die Uhrzeit heraus.
'''
def get_date(filename):

    # entfernt das Suffix .jpg
    split = filename.split('.')[0]
    
    # teilt den Dateinamen nach Unterstrichen auf
    split = split.split('_')
    
    if filename.startswith('Screenshot'):
        # Zweiter Teil des splits (split[1]) steht fürs Datum, dritter Teil (split[2]) für die Uhrzeit
        date_str = split[1] + split[2]
    else:
        # Zweiter Teil des splits (split[1]) steht fürs Datum, eine fiktive Uhrzeit 00:00:00 wird hinten dran gehängt
        date_str = split[1] + '000000'
        
    # Lese aus dem date_str mit dem Format YYMMDDHHMMSS das Datum und die Uhrzeit
    return datetime.strptime(date_str, '%Y%m%d%H%M%S').strftime("%Y:%m:%d %H:%M:%S")

if __name__ == '__main__':
    
    path = '/volume1/photo/'
#     path = '/localdata/src/python/nashome/photos'
    
    for currentpath, folders, files in os.walk(path):
        files[:] = [f for f in files if f.split('.')[-1] == 'jpg' and (f.split('-')[-1].startswith('WA') or f.startswith('Screenshot'))]
        
        for filename in files:
            old_fullpath = os.path.join(currentpath,filename)
            print(old_fullpath)
            
            # ersetzt alle Bindestriche durch Unterstriche
            newfilename = re.sub(r'-', '_', filename)
            
            # Extrahiere das Datum und die Uhrzeit aus dem Dateinamen
            exif_dict = {'Exif': { piexif.ExifIFD.DateTimeOriginal: get_date(newfilename) }}
            
            # ersetzt Screenshot_ durch IMG_
            newfilename = re.sub(r'Screenshot_', r'IMG_', newfilename)
            
            # Benennt die Dateien um
            new_fullpath = os.path.join(currentpath,newfilename)
            os.rename(old_fullpath, new_fullpath)
            
            # Fügt das Datum und die Uhrzeit als Meta-Daten in die Bild-Datei ein
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, new_fullpath)
            
            # Füge neue Dateienamen in den Index ein und lösche die alten aus dem Index
            subprocess.call(["synoindex", "-a", new_fullpath])
            subprocess.call(["synoindex", "-d", old_fullpath])
            
            print('Done!\n')      
