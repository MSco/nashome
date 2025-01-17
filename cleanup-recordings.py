#!/usr/bin/env python
'''
Created on 13.07.2022

@author: mschober
'''

import os
import click
import sys
import re

@click.command()
@click.argument('files', nargs=-1)
@click.option('-s', '--series', is_flag=True, help="Set this flag to rename series")
@click.option('-d', '--dash', is_flag=True, help="Set this flag if the series/movie name contains a dash")

def _main(files:list[str], series:bool, dash:bool):
    #     path = '/nashome/Serien/Die tollen Fußballstars/'
    extensions = ('.eit', '.ts', '.meta', '.jpg', '.txt')
    remove_extensions = ('.ap', '.cuts', '.sc', 'idx2')
    
    regex_eit = re.compile(b"^.*([0-9]+)\. Staffel, Folge ([0-9]+).*")
    regex_filename = re.compile(r"^.* - (.*) - (.*)\.eit" if dash else r"^.* - (.*)\.eit")
    
    remove_list = []
    rename_dict = {}
    touch_oldname_list = []
    
    for path in files:
        root:str = os.path.dirname(path)
        filename:str = os.path.basename(path)
        
        if filename.endswith(remove_extensions):
            remove_list.append(path)
        elif filename.endswith('eit'):
            match = regex_filename.match(filename.replace('_', ' '))
            name = match.group(1) + " - " + match.group(2) if dash else match.group(1)
            
            if series:
                with open(path, mode='rb') as file:
                    eit_content = file.read()
            
                match = regex_eit.match(eit_content)
                season = int(match.group(1).decode())
                episode = int(match.group(2).decode())
                    
                newname = "{} - s{:02d}e{:03d}".format(name, season, episode)
            else:
                newname = name
                
            basename = os.path.splitext(filename)[0]
            
            for oldname in [f for f in files if f.startswith(basename) and f.endswith(extensions)]:
                ext = os.path.splitext(oldname)[1]
                oldpath = os.path.join(root, oldname)
                newpath = os.path.join(root, newname + ext)
                rename_dict[oldpath] = newpath
                if not series and ext == '.ts':
                    touch_oldname_list.append(oldpath)
    
    if len(remove_list)==0 and len(rename_dict)==0:
        print("Nothing to do")
        sys.exit(0)
         
    for remove_path in remove_list:
        print("delete: {}".format(remove_path))
        
    for rename_path in rename_dict:    
        print("rename: {} -> {}".format(rename_path, rename_dict[rename_path]))
        
    for touch_path in touch_oldname_list: 
        oldname = os.path.basename(touch_path)
        txt_path = os.path.splitext(touch_path)[0] + '.oldname.txt'   
        print("create '{}' with content '{}'".format(txt_path, oldname))
        
    value_list = list(rename_dict.values())
    if (len(value_list) > len(set(value_list))):
        print("Aborting... Some files would be overwritten. Please see renaming list and check your input.") 
        sys.exit(1)

    print("Commands ok? [Y,n]")
    response = input()
    if len(response) == 0 or response.lower() == 'y':
        for remove_path in remove_list:
            print("removing {}".format(remove_path))
            os.remove(remove_path)
        for rename_path in rename_dict:    
            print("renaming {} -> {}".format(rename_path, rename_dict[rename_path]))
            os.rename(rename_path, rename_dict[rename_path])
        for touch_path in touch_oldname_list:
            oldname = os.path.basename(touch_path)
            txt_path = os.path.splitext(touch_path)[0] + '.oldname.txt'
            print("creating {}".format(txt_path))
            f = open(txt_path, "w")
            f.write(oldname)
    else:
        print("Nothing done!")
            
    
if __name__ == '__main__':
    _main()
    sys.exit(0)

