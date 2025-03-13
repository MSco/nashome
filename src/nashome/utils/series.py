import re

class Series():
    def __init__(self, name:str, series_id:int, *regex:tuple[str,...]) -> None:
        self.name = name
        self.series_id = series_id
        self.regex = regex if regex else [r"(.*)"]

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name
    
    def __eq__(self, other):
        return self.name == str(other)
    
    def build_episode_name(self, title:str) -> str:
        for regex in self.regex:
            episode_match = re.match(regex, title)
            if episode_match is not None:
                return re.match(regex, title).group(1).strip()
        
        return title.strip()