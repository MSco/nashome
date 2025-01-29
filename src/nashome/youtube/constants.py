from nashome.youtube.language import Language

LANGUAGES:list[Language] = [
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

PLAYLIST_FILENAME = "playlist.json"