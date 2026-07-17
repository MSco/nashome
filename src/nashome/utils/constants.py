from nashome.utils.series import Series
from nashome.youtube.language import Language

LANGUAGE_LIST:list[Language] = [
    Language(['german', 'deutsch', 'deu', 'ger', 'de'], 'de-DE'),
    Language(['english', 'englisch', 'en', 'eng', 'us'], 'en'),
    Language(['italian', 'italienisch', 'it', 'ita'], 'it'),
    Language(['spanish', 'spanisch', 'spa', 'es'], 'es-ES'),
    Language(['portuguese', 'portugiesisch', 'pt', 'por'], 'pt-PT'),
    Language(['french', 'französisch', 'fr', 'fra'], 'fr-FR'),
    Language(['arabic', 'arabisch', 'ar', 'ara'], 'ar'),
    Language(['dansk', 'dänisch', 'da', 'dan'], 'da'),
    Language(['finnish', 'finnisch', 'fi', 'fin'], 'fi'),
    Language(['hebrew', 'hebräisch', 'iw', 'heb'], 'iw'),
    Language(['dutch', 'niederländisch', 'holländisch', 'nl', 'nld'], 'nl'),
    Language(['norwegian', 'norwegisch', 'no', 'nor'], 'no'),
    Language(['polish', 'polnisch', 'pl', 'pol'], 'pl'),
    Language(['portuguese brazilian', 'portugiesisch brasilianisch', 'pt-BR', 'ptbr'], 'pt-BR'),
    Language(['portuguese', 'portugiesisch', 'pt-PT', 'ptpt'], 'pt-PT'),
    Language(['swedish', 'schwedisch', 'sv', 'swe'], 'sv-SE')
]

# https://developer.themoviedb.org/reference/search-tv
# https://developer.themoviedb.org/reference/tv-season-details
SERIES_LIST:list[Series] = [
    Series("Pokemon Horizonte", 220150, r".* Folge \d+ \|(.*?)\|.*"),
    Series("Pokemon", 60572, r"(.*?)\|.*", r".*_S\d+E\d+_(.*?)\.(mp4|mkv)"),
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
    Series("Teenage Mutant Ninja Turtles", 160, r".*_S\d+E\d+_(.*?)\.mp4"),
    Series("Dragon Ball Z", 12971),
    Series("Dragon Ball Super", 62715),
    Series("Dragon Ball", 12609),
    Series("House of Cards", 1425),
    Series("Sisi", 153282),
    Series("Die tollen Fußballstars", 25707),
    Series("Captain Tsubasa - Super Kickers 2006", 24106),
    Series("Captain Tsubasa", 77240),
    Series("Chernobyl", 87108),
    Series("Ich heirate eine Familie", 36778),
    Series("Mila Superstar", 46348),
    Series("Pippi Langstrumpf", 3714),
    Series("Paw Patrol", 57532),
    Series("Rubble & Crew", 214875),
    Series("Bibi Blocksberg", 63361),
    Series("Bibi und Tina", 61205)
]

TEMPLATE_START_DIRNAME = "start"
TEMPLATE_END_DIRNAME = "end"

STORED_VIDEOS_FILENAME = "stored_videos.json"