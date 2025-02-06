from nashome.utils.series import Series
from nashome.youtube.language import Language


LANGUAGE_LIST:list[Language] = [
    Language(['german', 'deutsch'], ['deu', 'ger', 'de']),
    Language(['english', 'englisch'], ['en', 'eng', 'us']),
    Language(['italian', 'italienisch'], ['it', 'ita']),
    Language(['spanish', 'spanisch'], ['spa', 'es']),
    Language(['portuguese', 'portugiesisch'], ['pt', 'por']),
    Language(['french', 'französisch'], ['fr', 'fra']),
    Language(['russian', 'russisch'], ['ru', 'rus']),
    Language(['chinese', 'chinesisch'], ['zh', 'chi']),
    Language(['japanese', 'japanisch'], ['ja', 'jpn']),
    Language(['korean', 'koreanisch'], ['ko', 'kor']), 
    Language(['arabic', 'arabisch'], ['ar', 'ara']),
    Language(['turkish', 'türkisch'], ['tr', 'tur']),
    Language(['hindi'], ['hi', 'hin']),
    Language(['bengali'], ['bn', 'ben']),
    Language(['urdu'], ['ur', 'urd']),
    Language(['indonesian'], ['id', 'ind']),
    Language(['malay'], ['ms', 'may']),
    Language(['vietnamese'], ['vi', 'vie']),
    Language(['thai'], ['th', 'tha']),
    Language(['swahili'], ['sw', 'swa']),
]

# https://developer.themoviedb.org/reference/search-tv
# https://developer.themoviedb.org/reference/tv-season-details
SERIES_LIST:list[Series] = [
    Series("Pokemon Horizonte", 220150),
    Series("Pokemon", 60572, r"(.*?)\|.*"),
    Series("Die Kickers", 64049),
    Series("Paw Patrol", 57532, r".*\|(.*)\|.*"),
    Series("PJ Masks", 65417, r"(?:Ganze Folge:*)?(.*?)[^\u0000-\uFFFF].*"),
    Series("My Hero Academia", 65930),
    Series("SpongeBob Schwammkopf", 387)
]

STORED_VIDEOS_FILENAME = "stored_videos.json"