"""
This module contains the Language class.
"""

class Language():
    def __init__(self, long:list[str], short:list[str]):
        """
        Initialize a Language object.
        """
        self.long = list(map(str.lower, long))
        self.short = list(map(str.lower, short))

    def __str__(self):
        """
        Return the long language name.
        """
        return self.long + self.short

    def __repr__(self):
        """
        Return the long language name.
        """
        return self.long

    def __eq__(self, other:str):
        """
        Check if the language name is equal to another language name.
        """
        return other.lower() in self

    def __contains__(self, other:str):
        """
        Check if the language name is contained in another language name.
        """
        return other.lower() in self.long or other.lower() in self.short