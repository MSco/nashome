'''
Created on 09.09.2020

@author: mschober
'''

import os

if __name__ == '__main__':
    
    path = '/nas/FRITZ.NAS/Filme/Filme'
    
    movie_extensions = ['.ts', '.mkv', '.avi', '.mp4']
    misc_extensions = ['.jpg', '.eit', '.cuts', '.ap', '.meta', '.sc', '.log', '.txt', '.nfo', '.backup', '.idx2']
    
    for currentpath, folders, files in sorted(os.walk(path)):
        for file in files:
            movie_path = os.path.join(currentpath, file)
            if movie_path.endswith(tuple(movie_extensions)):
                print(movie_path)
                text_file_name = os.path.join(currentpath, file+".oldname.txt")
#                 print(text_file_name)
                with open(text_file_name, "w") as text_file:
                    text_file.write(file + '\n')
                

    