from pytubefix import YouTube
import re
import requests
from unidecode import unidecode

from nashome.config.config import tmdb_api_token

def build_filename_for_youtube(yt:YouTube, audio_only:bool):
    title = yt.title
    suffix = 'm4a' if audio_only else 'mp4'
    return build_filename(title=title, suffix=suffix, language_code='en-US')

def build_filename(title:str, suffix:str, language_code:str):
    # dict = { series_name: [series_id, num_seasons] }
    dict_series = {
        'Pokemon Horizonte': [220150, 1],
        'Pokemon': [60572, 25]
    }
    
    output_filename = None
    for series_name in dict_series.keys():
        if filter_string(series_name) in filter_string(title):
            episode, season = find_episode_and_season(title=title, series_id=dict_series[series_name][0], num_seasons=dict_series[series_name][1], language_code=language_code)
            if not episode or not season:
                continue
            output_filename = f'{series_name} - s{season:02d}e{episode:03d}.{suffix}'
            break
    else:
        output_filename = f'{title}.{suffix}'

    return output_filename

def extract_episode_name(title:str):
    episode_name = filter_string(title)

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