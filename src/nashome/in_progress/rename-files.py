'''
Created on 09.09.2020

@author: mschober
'''

import os
import re
import collections
from fileinput import filename

if __name__ == '__main__':
    
    path = '/nas/FRITZ.NAS/Filme/Filme'
#     path = '/localdata/data/movies/'
    
    movie_extensions = ['.ts', '.mkv', '.avi', '.mp4']
    misc_extensions = ['.jpg', '.eit', '.cuts', '.ap', '.meta', '.sc', '.log', '.txt', '.nfo', '.backup', '.idx2']
    
    movie_list = []
    
    for currentpath, folders, files in sorted(os.walk(path)):
        for old_filename in files:
            movie_path = os.path.join(currentpath, old_filename)
            if movie_path.endswith(tuple(movie_extensions)) or movie_path.endswith(tuple(misc_extensions)) and not old_filename == 'folder.jpg' and not movie_path.endswith('oldname.txt'):

                # OTR Replacement
                new_filename = re.sub(r'_(\d{2})\.(\d{2})\.(\d{2})_(\d{2})-(\d{2})_[A-Za-z0-9]+_[0-9]+_Tvoon_De\.Mpg', '.OTR', old_filename)

                new_filename = re.sub(r'.*HD[^-]*-[_ ].*?', '', new_filename)
                new_filename = re.sub(r'_', ' ', new_filename)
                new_filename = re.sub(r',_', '_', new_filename)
                no_ext = os.path.splitext(new_filename)
                new_filename = no_ext[0].title() + no_ext[1]
                new_filename = re.sub(r'Iii', 'III', new_filename)
                new_filename = re.sub(r'Ii', 'II', new_filename)
                new_filename = re.sub(r'Vii', 'VII', new_filename)
                new_filename = re.sub(r'Oldname.txt', 'oldname.txt', new_filename)
                new_filename = re.sub(r'__', '_-_', new_filename)
                new_filename = re.sub(r'\.Joined\.', '.', new_filename)
                new_filename = re.sub(r'\.Cut\.', '.', new_filename)
                new_filename = re.sub(r'\!+', '', new_filename)
                new_filename = re.sub(r'Otr', 'OTR', new_filename)
                new_filename = re.sub(r'Hq', 'HQ', new_filename)
                new_filename = re.sub(r'Hd', 'HD', new_filename)
                
                movie_list.append(new_filename)
                
                print(movie_path + " -> " + new_filename)
                os.rename(movie_path, os.path.join(currentpath, new_filename))
                
    print("Duplicate filenames: ")            
    print([item for item, count in collections.Counter(movie_list).items() if count > 1])

