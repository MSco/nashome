"""
This module contains the Language class.
"""

class Language():
    def __init__(self, synonyms:list[str], code:str):
        """
        Initialize a Language object.
        """
        self.synonyms = list(map(str.lower, synonyms))
        self.code = code

    def __str__(self):
        """
        Return the language code.
        """
        return self.code

    def __repr__(self):
        """
        Return the language code.
        """
        return self.code

    def __eq__(self, other:str):
        """
        Check if the language name is equal to another language name.
        """
        return other.lower() in self

    def __contains__(self, other:str):
        """
        Check if the language name is contained in another language name.
        """
        return other.lower() in self.synonyms