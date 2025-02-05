from pathlib import Path
from pytubefix import YouTube
import re
import requests
from unidecode import unidecode

from nashome.config.config import tmdb_api_token

def build_filename_from_youtube(yt:YouTube, audio_only:bool):
    suffix = 'm4a' if audio_only else 'mp4'
    episode_name = extract_episode_name_from_youtube(yt.title)
    filestem = build_filestem(original_title=yt.title, episode_name=episode_name, language_code='en-US')
    return f"{filestem}.{suffix}"

def build_filestem_from_epgfile(series_name:str, epg_path:str|Path):
    regex_epg = re.compile(b"^.*([0-9]+)\. Staffel, Folge ([0-9]+).*")
    
    epg_file = open(epg_path, mode='rb')
    epg_content = epg_file.read()
    
    match_epg = regex_epg.match(epg_content)
    if match_epg is not None: 
        season = int(match_epg.group(1).decode())
        episode = int(match_epg.group(2).decode())
        
        return f"{series_name} - s{season:02d}e{episode:03d}"
    else:
        episode_name = extract_episode_name_from_epgcontent(epg_content)
        if not episode_name:
            episode_name = series_name
        return build_filestem(original_title=series_name, episode_name=episode_name, language_code='de-DE')

def build_filestem(original_title:str, episode_name:str, language_code:str):
    # dict = { series_name: [series_id, num_seasons] }
    dict_series = {
        'Pokemon Horizonte': [220150, 1],
        'Pokemon': [60572, 25]
    }
    
    output_filestem = None
    for series_name in dict_series.keys():
        if filter_string(series_name) in filter_string(original_title):
            episode, season = find_episode_and_season(title=episode_name, series_id=dict_series[series_name][0], num_seasons=dict_series[series_name][1], language_code=language_code)
            if not episode or not season:
                continue
            output_filestem = f'{series_name} - s{season:02d}e{episode:03d}'
            break
    else:
        output_filestem = f'{episode_name}'

    return output_filestem

def extract_episode_name_from_youtube(title:str) -> str:
    episode_name = filter_string(title)
    return episode_name.split("|")[0].strip()

def extract_episode_name_from_epgcontent(content:str) -> str:
    filtered_content = filter_string(content)
    match_episode = re.match(r".*<x>schedule</x>(.*?)\x00", filtered_content)
    if match_episode is not None:
        return match_episode.group(1)
    
    return None

def find_episode_and_season(title:str, series_id:int, num_seasons:int, language_code:str):
    # https://developer.themoviedb.org/reference/search-tv
    # https://developer.themoviedb.org/reference/tv-season-details

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
            if tmdb_episode_name in title or title.split("|")[0].strip() in tmdb_episode_name:
                print(f"TMDB: found {episode['name']} as s{season:02}e{episode['episode_number']:03d}.")
                return episode['episode_number'], episode['season_number']
    return None, None

def filter_string(string:str|bytes) -> str:
    if isinstance(string, bytes):
        string = string.decode('utf-8', 'ignore')

    keyword_replace = {
        r"_" : "",
        r"\'" : "",
        r"\." : "",
        r"\!": "",
        r"\-" : "",
        r"\," : "",
        r"versus" : "vs",
        r"\&" : "and",
        r"\s+": " "
    }

    filtered_string = unidecode(string.lower())
    for key, value in keyword_replace.items():
        filtered_string = re.sub(key, value, filtered_string)

    return filtered_string.strip()

def cleanup_recordings(paths:list[Path], series:bool, dash:bool):
    extensions = ('.eit', '.ts', '.meta', '.jpg', '.txt')
    remove_extensions = ('.ap', '.cuts', '.sc', 'idx2')
    
    regex_filename = re.compile(r"^.* - (.*) - (.*)\.eit" if dash else r"^.* - (.*)\.eit")
    
    remove_list:list[Path] = []
    rename_dict:dict[Path, Path] = {}
    touch_oldname_list:list[Path] = []
    
    for path in paths:
        root = path.parent
        filename = path.name
        
        if filename.endswith(remove_extensions):
            remove_list.append(path)
        elif filename.endswith('eit'):
            match_filename = regex_filename.match(filename.replace('_', ' '))
            name = match_filename.group(1) + " - " + match_filename.group(2) if dash else match_filename.group(1)
            
            if series:
                newstem = build_filestem_from_epgfile(name, path)
            else:
                newstem = name
                
            basename = path.stem
            
            for oldpath in [p for p in paths if p.name.startswith(basename) and p.name.endswith(extensions)]:
                suffix = "".join(oldpath.suffixes)
                newpath = root/(newstem + suffix)
                rename_dict[oldpath] = newpath
                if not series and suffix == '.ts':
                    touch_oldname_list.append(oldpath)
    
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

    print("Commands ok? [Y,n]")
    response = input()
    if len(response) == 0 or response.lower() == 'y':
        for remove_path in remove_list:
            print("removing {}".format(remove_path))
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