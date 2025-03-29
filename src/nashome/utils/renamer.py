from pathlib import Path
import re
import requests
from unidecode import unidecode

from nashome.config.config import tmdb_api_token
from nashome.utils.constants import SERIES_LIST
from nashome.utils.eit import EitContent
from nashome.utils.series import Series

def build_filename_from_title(title:str, suffix:str, language_code:str, try_all_seasons:bool) -> tuple[str, str]:
    if suffix.startswith('.'):
        suffix = suffix[1:]
    series = find_series(title)
    episode_name = series.build_episode_name(title) if series else title
    filestem, episode_name = build_filestem(original_title=title, episode_name=episode_name, language_code=language_code, try_all_seasons=try_all_seasons)
    return f"{filestem}.{suffix}", (episode_name if series else None)

def build_filestem_from_eitfile(eit_path:str|Path, force_tmdb:bool, series:bool) -> tuple[str, str]:
    eit_content = EitContent(eit_path)
    name = replace_forbidden_characters(eit_content.getEitName())

    if name and not series:
        return name, None

    regex_episode_number = re.compile(r"^.*([0-9]+)\. Staffel, Folge ([0-9]+).*")
    
    match_episode_number = regex_episode_number.match(eit_content.getEitDescription())
    if not force_tmdb and match_episode_number is not None: 
        season = int(match_episode_number.group(1))
        episode = int(match_episode_number.group(2))
        
        return f"{name} - s{season:02d}e{episode:03d} - {eit_content.getEitShortDescription()}", eit_content.getEitShortDescription()
    else:
        episode_name = eit_content.getEitShortDescription()
        if not episode_name:
            episode_name = name
        return build_filestem(original_title=name, episode_name=episode_name, language_code='de-DE', try_all_seasons=True)

def build_filestem_from_oldname(filename:str, dash:bool, series:bool) -> tuple[str, str]:
    if series:
        regex_series = re.compile(rf"(.*)_S(\d+)E(\d+)_(.*)")
        episode_match = regex_series.match(filename)
        if episode_match is not None:
            new_name = f"{episode_match.group(1)} - s{int(episode_match.group(2)):02d}e{int(episode_match.group(3)):03d} - {episode_match.group(4)}"
            return new_name, None

    regex_filename = re.compile(r"^.* - (.*) - (.*)\.eit" if dash else r"^.* - (.*)\.eit")
    match_filename = regex_filename.match(filename.replace('_', ' '))
    if match_filename is None:
        return Path(filename).stem, None
    name = match_filename.group(1) + " - " + match_filename.group(2) if dash else match_filename.group(1)
    return name, None

def build_filestem(original_title:str, episode_name:str, language_code:str, try_all_seasons:bool) -> tuple[str, str]:
    series = find_series(original_title)
    
    if series:
        season_id = 0 if try_all_seasons else get_season_id(original_title) 
        episode, season, episode_name = find_episode_and_season(title=episode_name, series_id=series.series_id, season_id=season_id, language_code=language_code)
        if episode and season and episode_name:
            return f'{series.name} - s{season:02d}e{episode:03d} - {replace_forbidden_characters(episode_name)}', episode_name

    return replace_forbidden_characters(original_title), episode_name

def get_season_id(title:str) -> int:
    regex_list_season = [re.compile(r".*s(\d+)e\d+.*"), re.compile(r".*staffel (\d+).*"), re.compile(r".*season (\d+).*")]
    for regex in regex_list_season:
        match = regex.match(title.lower())
        if match:
            print(f"Found season id {int(match.group(1))}.")
            return int(match.group(1))
    return 0

def replace_forbidden_characters(string:str) -> str:
    keyword_replace = {
        "/" : "-",
        ":" : "",
        "?" : "",
        "*" : "",
        '"' : "",
        "'" : "",
        "<" : "-",
        ">" : "-",
        "|" : "-",
        "\\" : "-"
    }

    for key, value in keyword_replace.items():
        string = string.replace(key, value)
    
    return string

def filter_string(string:str|bytes) -> str:
    if isinstance(string, bytes):
        string = string.decode('utf-8', 'ignore')

    keyword_replace = {
        r"_" : "",
        r"\'" : "",
        r"\." : "",
        r"\!": "",
        r"\?" : "",
        r"\-" : " ",
        r"\," : " ",
        r"\:" : "",
        r'"' : "",
        r"'" : "",
        r"versus" : "vs",
        r"\&" : "and",
        r"\s+": ""
    }

    filtered_string = unidecode(string.lower())
    for key, value in keyword_replace.items():
        filtered_string = re.sub(key, value, filtered_string)

    return filtered_string.strip()

def find_episode_and_season(title:str, series_id:int, season_id:int, language_code:str) -> tuple[int, int, str]:
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {tmdb_api_token}"
    }
    
    if season_id:
        season_list = [season_id]
    else:
        url = f"https://api.themoviedb.org/3/tv/{series_id}?language={language_code}"

        response = requests.get(url, headers=headers)
        num_seasons = response.json()["number_of_seasons"]
        print(f"TMDB: found series '{response.json()['name']}' with {num_seasons} seasons.")
        season_list = list(range(1, num_seasons+1))

    for season in season_list:
        url = f"https://api.themoviedb.org/3/tv/{series_id}/season/{season}?language={language_code}"
        response = requests.get(url, headers=headers)
        for episode in response.json()['episodes']:
            tmdb_episode_name = filter_string(episode['name'])
            title = filter_string(title)
            if not tmdb_episode_name or not title:
                continue
            if tmdb_episode_name in title or title in tmdb_episode_name:
                episode_name = episode['name']
                print(f"TMDB: found episode '{episode_name}' as s{season:02}e{episode['episode_number']:03d}.")
                if not language_code == 'de-DE':
                    episode_name = find_episode_name(series_id, season, episode['episode_number'], "de-DE")
                return episode['episode_number'], episode['season_number'], episode_name
    return None, None, None

def find_episode_name(series_id:int, season_id:int, episode_id:int, language_code:str="de-DE") -> str:
    url = f"https://api.themoviedb.org/3/tv/{series_id}/season/{season_id}/episode/{episode_id}?language={language_code}"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {tmdb_api_token}",
        "Cache-Control": "no-cache"
    }
    response = requests.get(url, headers=headers)
    return response.json()["name"]

def find_series(title:str) -> Series:
    for series in SERIES_LIST:
        if filter_string(series.name) in filter_string(title):
            return series
    return None

def cleanup_recordings(paths:list[Path], series:bool, force_tmdb:bool, force_rename:bool, dash:bool=False, no_tmdb:bool=False, language_code:str='de-DE', try_all_seasons:bool=False) -> bool:
    extensions = ('.eit', '.ts', '.meta', '.jpg', '.txt')
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
            if no_tmdb:
                newstem,_ = build_filestem_from_oldname(filename, dash, series)
            else:
                newstem,_ = build_filestem_from_eitfile(path, force_tmdb, series)
            basename = path.stem
            
            for oldpath in [p for p in paths if p.name.startswith(basename) and p.name.endswith(extensions)]:
                suffix = "".join(oldpath.suffixes)
                newpath = root/(newstem + suffix)
                rename_dict[oldpath] = newpath
                if not series and suffix == '.ts':
                    touch_oldname_list.append(oldpath)
        elif filename.endswith(('.mp4', '.mkv')):
            if no_tmdb:
                newstem,_ = build_filestem_from_oldname(filename, dash, series)
            else:
                newstem,_ = build_filename_from_title(filename, path.suffix, language_code, try_all_seasons)
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