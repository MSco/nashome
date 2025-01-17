'''
Created on 09.09.2020

@author: mschober
'''

import os
import re
import collections
import numpy as np
import exifread
import time
import datetime

if __name__ == '__main__':
    
#    path = '/volume1/photo/'
    path = '/nashome/photo/'
    extensions = ['.jpg', '.jpeg', '.JPG', '.JPEG']
    exclude = '@eaDir'
    
    list_of_folders = []
    
    for currentpath, folders, files in os.walk(path):
        folders[:] = [d for d in folders if d not in exclude]
        
        lastdate = ''
        print(currentpath)
        
        album_tuple = [lastdate, currentpath]
        
        for filename in files:
            if filename.endswith(tuple(extensions)):
                
                filepath = os.path.join(currentpath, filename)
                f = open(filepath, 'rb')
                try:
                    tags = exifread.process_file(f)
                except:
                    tags = {}
                f.close()
                
                if 'EXIF DateTimeOriginal' in tags:
                    currentdate = tags['EXIF DateTimeOriginal'].values
                    
                    if currentdate > lastdate:
                        lastdate = currentdate
        

        album_tuple[0] = lastdate
        list_of_folders.append(album_tuple)
        
        print(lastdate)
        
    print('---------')
    print('set album dates:')
    
    sorted_list_of_folders = sorted(list_of_folders)
    
    for album in sorted_list_of_folders:
        date = album[0]
        foldername = album[1]
        print(foldername)
        
        try:
            date_obj = datetime.datetime.strptime(date, '%Y:%m:%d %H:%M:%S')
            modTime = time.mktime(date_obj.timetuple())
            os.utime(foldername, (modTime, modTime))
            time.sleep(2)
        except ValueError:
            print("no date found")
        
        
