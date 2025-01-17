'''
Created on 25.10.2020

@author: Puddies, synology-forum.de
@version: 1.0.0-20201109
'''

from mutagen.easyid3 import EasyID3
import os

# Konsole eyeD3:
# for I in {01..10}; do eyeD3 -a "Benjamin Blümchen" -A "Benjamin Blümchen als Weihnachtsmann" -t "Track $I" -n $I -N 10 "Track$I.mp3" -2; done

if __name__ == '__main__':
    
    path = '/nashome/Zwischenspeicher/Rolf Zukowski - Winterkinder/'
#     path = '/localdata/src/python/nashome/photos'
    
    for currentpath, folders, files in os.walk(path):
        
        for filename in files:
            
            fullpath = os.path.join(currentpath,filename)
            print(fullpath)
            
            audio = EasyID3(fullpath)
            audio['artist'] = u'Rolf Zuckowski'
            audio['album'] = u'Winterkinder'
#             audio['comments'] = u''
#             audio['year'] = u'1987'
            audio['genre'] = u'Kindermusik'
            audio['title'] = (filename.split(' - ')[1]).split('.')[0]
            audio.save()
            
            print('Done!\n')      
