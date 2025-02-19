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
    Series("Pokemon Horizonte", 220150, r".* Folge \d+ \|(.*?)\|.*"),
    Series("Pokemon", 60572, r"(.*?)\|.*"),
    Series("Die Kickers", 64049, r"Die Kickers - (.*) Folge \d+"),
    Series("Paw Patrol", 57532, r".*\|(.*)\|.*"),
    Series("PJ Masks", 65417, r"(?:Ganze Folge:*)?(.*?)[^\u0000-\uFFFF].*"),
    Series("My Hero Academia", 65930),
    Series("SpongeBob Schwammkopf", 387),
    Series("Desperate Housewives", 693),
    Series("Sex and the City", 105),
    Series("And Just Like That", 116450),
    Series("The Big Bang Theory", 1418),
    Series("House of the Dragon", 94997),
    Series("Game of Thrones", 1399),
    Series("The Lazarus Project", 194567),
    Series("Almania", 121062),
    Series("Lieselotte", 105110),
    Series("Mega Man", 1323),
    Series("Teenage Mutant Ninja Turtles", 160, r".*_S\d+E\d+_(.*)\.mp4"),
]

TEMPLATE_START_DIRNAME = "start"
TEMPLATE_END_DIRNAME = "end"

STORED_VIDEOS_FILENAME = "stored_videos.json"