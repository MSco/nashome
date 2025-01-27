import re

class ImageFilenamePattern():
    def __init__(self, pattern:re.Pattern, change_exif: bool) -> None:
        self.pattern = pattern
        self.change_exif = change_exif