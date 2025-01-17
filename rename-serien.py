'''
Created on 09.09.2020

@author: mschober
'''

import os
import re
import collections
import numpy as np

if __name__ == '__main__':
    
#     path = '/nashome/Serien/Die tollen Fußballstars/'
    path = '/localdata/tocut/Familie/'
    extensions = ['.eit', '.ts', '.meta']
    
    # Episoden pro Staffel
    season_sizes = [5, 5, 2, 5] 
    old_filename_start = 'Ich heirate eine Familie'
    new_filename_start = 'Ich heirate eine Familie'
    
    # Erste verfügbare Folge
    season_idx = 1
    episode_idx = 1
    overall_idx = 1
    
    for currentpath, folders, files in sorted(os.walk(path)):
        files.sort()
        for old_filename in files:
            movie_path = os.path.join(currentpath, old_filename)
            if movie_path.endswith(tuple(extensions)) and old_filename_start in old_filename:

                ext_split = os.path.splitext(old_filename)

                summe = np.sum(season_sizes[:season_idx])
                if overall_idx > summe:
                    season_idx += 1
                    episode_idx = 1
                    
                new_filename = new_filename_start + ' - s' + f'{season_idx:02d}' + 'e' + f'{episode_idx:02d}' + ext_split[1]
                    
                print(old_filename + ' -> ' + new_filename)
                
                os.rename(movie_path, os.path.join(currentpath, new_filename))

                if ext_split[1] == extensions[-1]:
                    episode_idx += 1                    
                    overall_idx += 1
