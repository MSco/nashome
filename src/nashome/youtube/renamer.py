from pytubefix import YouTube
import requests
from unidecode import unidecode

from nashome.config.config import tmdb_api_token

def generate_filename(yt:YouTube, audio_only:bool):
    dict_series = {
        'Pokemon': 60572,
    }
    suffix = 'm4a' if audio_only else 'mp4'
    output_filename = None
    for title_name in dict_series.keys():
        if title_name.lower() in unidecode(yt.title).lower():
            episode, season = find_episode_and_season(title=yt.title, series_id=dict_series[title_name])
            if not episode or not season:
                continue
            output_filename = f'{title_name} - s{season:02d}e{episode:03d}.{suffix}'
            break
    else:
        output_filename = f'{yt.title}.{suffix}'

    return output_filename

def find_episode_and_season(title:str, series_id:int):
    # https://developer.themoviedb.org/reference/search-tv
    # https://developer.themoviedb.org/reference/tv-season-details

    num_seasons = 25
    for season in range(1, num_seasons+1):
        url = f"https://api.themoviedb.org/3/tv/{series_id}/season/{season}?language=en-US"
        headers = {
                    "accept": "application/json",
                    "Authorization": f"Bearer {tmdb_api_token}"
                }
        response = requests.get(url, headers=headers)
        for episode in response.json()['episodes']:
            tmdb_episode_name = unidecode(episode['name']).lower()
            title = unidecode(title).lower()
            if tmdb_episode_name in title or any([part in tmdb_episode_name for part in map(str.strip,title.split("|"))]):
                print(f"TMDB: found {episode['name']} as s{season:02}e{episode['episode_number']:03d}.")
                return episode['episode_number'], episode['season_number']
    return None, None