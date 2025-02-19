from pathlib import Path
import re
import requests
from unidecode import unidecode

from nashome.config.config import tmdb_api_token
from nashome.utils.constants import SERIES_LIST
from nashome.utils.eit import EitContent
from nashome.utils.series import Series

def build_filename_from_title(title:str, audio_only:bool, language_code:str):
    suffix = 'm4a' if audio_only else 'mp4'
    series = find_series(title)
    episode_name = series.build_episode_name(title) if series else title
    filestem = build_filestem(original_title=title, episode_name=episode_name, language_code=language_code)
    return f"{filestem}.{suffix}"

def build_filestem_from_eitfile(eit_path:str|Path, force_tmdb:bool, series:bool):
    eit_content = EitContent(eit_path)
    name = eit_content.getEitName().replace(":", " -")

    if name and not series:
        return name

    regex_episode_number = re.compile(r"^.*([0-9]+)\. Staffel, Folge ([0-9]+).*")
    
    match_episode_number = regex_episode_number.match(eit_content.getEitDescription())
    if not force_tmdb and match_episode_number is not None: 
        season = int(match_episode_number.group(1))
        episode = int(match_episode_number.group(2))
        
        return f"{name} - s{season:02d}e{episode:03d}"
    else:
        episode_name = eit_content.getEitShortDescription()
        if not episode_name:
            episode_name = name
        return build_filestem(original_title=name, episode_name=episode_name, language_code='de-DE')

def build_filestem_from_oldname(filename:str, dash:bool):
    regex_filename = re.compile(r"^.* - (.*) - (.*)\.eit" if dash else r"^.* - (.*)\.eit")
    match_filename = regex_filename.match(filename.replace('_', ' '))
    if match_filename is None:
        return Path(filename).stem
    name = match_filename.group(1) + " - " + match_filename.group(2) if dash else match_filename.group(1)
    return name

def build_filestem(original_title:str, episode_name:str, language_code:str):
    series = find_series(original_title)
    
    if series:
        episode, season = find_episode_and_season(title=episode_name, series_id=series.series_id, language_code=language_code)
        if episode and season:
            return f'{series.name} - s{season:02d}e{episode:03d}'

    return original_title

def filter_string(string:str|bytes) -> str:
    if isinstance(string, bytes):
        string = string.decode('utf-8', 'ignore')

    keyword_replace = {
        r"_" : "",
        r"\'" : "",
        r"\." : "",
        r"\!": "",
        r"\-" : " ",
        r"\," : "",
        r"\:" : "",
        r"versus" : "vs",
        r"\&" : "and",
        r"\s+": " "
    }

    filtered_string = unidecode(string.lower())
    for key, value in keyword_replace.items():
        filtered_string = re.sub(key, value, filtered_string)

    return filtered_string.strip()

def find_episode_and_season(title:str, series_id:int, language_code:str):
    url = f"https://api.themoviedb.org/3/tv/{series_id}?language={language_code}"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {tmdb_api_token}"
    }

    response = requests.get(url, headers=headers)
    num_seasons = response.json()["number_of_seasons"]
    print(f"TMDB: found series '{response.json()['name']}' with {num_seasons} seasons.")

    for season in range(1, num_seasons+1):
        url = f"https://api.themoviedb.org/3/tv/{series_id}/season/{season}?language={language_code}"
        headers = {
                    "accept": "application/json",
                    "Authorization": f"Bearer {tmdb_api_token}"
                }
        response = requests.get(url, headers=headers)
        for episode in response.json()['episodes']:
            tmdb_episode_name = filter_string(episode['name'])
            title = filter_string(title)
            if not tmdb_episode_name or not title:
                continue
            if tmdb_episode_name in title or title in tmdb_episode_name:
                print(f"TMDB: found episode '{episode['name']}' as s{season:02}e{episode['episode_number']:03d}.")
                return episode['episode_number'], episode['season_number']
    return None, None

def find_series(title:str) -> Series:
    for series in SERIES_LIST:
        if filter_string(series.name) in filter_string(title):
            return series
    return None

def cleanup_recordings(paths:list[Path], series:bool, force_tmdb:bool, force_rename:bool, dash:bool=False, no_eit:bool=False, language_code:str='de-DE'):
    extensions = ('.eit', '.ts', '.meta', '.jpg', '.txt', '.mp4')
    remove_extensions = ('.ap', '.cuts', '.sc', 'idx2')
    
    remove_list:list[Path] = []
    rename_dict:dict[Path, Path] = {}
    touch_oldname_list:list[Path] = []
    
    for path in paths:
        root = path.parent
        filename = path.name
        
        if filename.endswith(remove_extensions):
            remove_list.append(path)
        elif filename.endswith('eit'):
            if no_eit:
                newstem = build_filestem_from_oldname(filename, dash)
            else:
                newstem = build_filestem_from_eitfile(path, force_tmdb, series)
            basename = path.stem
            
            for oldpath in [p for p in paths if p.name.startswith(basename) and p.name.endswith(extensions)]:
                suffix = "".join(oldpath.suffixes)
                newpath = root/(newstem + suffix)
                rename_dict[oldpath] = newpath
                if not series and suffix == '.ts':
                    touch_oldname_list.append(oldpath)
        elif filename.endswith('.mp4'):
            newstem = build_filename_from_title(filename, False, language_code)
            rename_dict[path] = root / newstem
    
    if len(remove_list)==0 and len(rename_dict)==0:
        print("Nothing to do")
        return True
         
    for remove_path in remove_list:
        print(f"delete: {remove_path}")
        
    for rename_path in rename_dict:    
        print(f"rename: {rename_path} -> {rename_dict[rename_path]}")
        
    for touch_path in touch_oldname_list: 
        txt_path = touch_path.with_suffix('.oldname.txt')
        print(f"create '{txt_path}' with content '{touch_path.name}'")
        
    value_list = list(rename_dict.values())
    if (len(value_list) > len(set(value_list))):
        print("Aborting... Some files would be overwritten. Please see renaming list and check your input.") 
        return False

    if force_rename:
        response = 'y'
    else:
        print("Commands ok? [Y,n]")
        response = input()
    if len(response) == 0 or response.lower() == 'y':
        for remove_path in remove_list:
            print(f"removing {remove_path}")
            remove_path.unlink()
        for rename_path in rename_dict:    
            print(f"renaming {rename_path} -> {rename_dict[rename_path]}")
            rename_path.rename(rename_dict[rename_path])
        for touch_path in touch_oldname_list:
            oldname = touch_path.name
            txt_path = touch_path.with_suffix('.oldname.txt')
            print(f"creating {txt_path}")
            f = open(txt_path, "w")
            f.write(oldname)
    else:
        print("Nothing done!")