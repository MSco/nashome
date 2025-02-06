import re

class Series():
    def __init__(self, name:str, series_id:int, regex:str=r"(.*)"):
        self.name = name
        self.series_id = series_id
        self.regex = regex

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name
    
    def __eq__(self, other):
        return self.name == str(other)
    
    def build_episode_name(self, title:str) -> str:
        episode_match = re.match(self.regex, title)
        if episode_match is not None:
            return re.match(self.regex, title).group(1).strip()
        return title.strip()