from typing import List

from kata.domain.models import KataLanguage, KataTemplate


class KataError(Exception):
    pass


class InvalidKataName(KataError):
    def __init__(self, kata_name: str, reason=None):
        super().__init__(f"Kata name '{kata_name}' is invalid!")
        self.kata_name = kata_name
        self.reason = reason


class KataLanguageNotFound(KataError):
    def __init__(self, available_languages: List[KataLanguage] = None):
        self.available_languages = available_languages


class KataTemplateNotFound(KataError):
    def __init__(self, available_templates: List[KataTemplate] = None):
        self.available_templates = available_templates


class InvalidConfig(KataError):
    pass


class ApiError(KataError):
    pass


class ApiLimitReached(ApiError):
    def __init__(self):
        super().__init__("Api limit has been reached")


class InvalidAuthToken(ApiError):
    def __init__(self, token):
        super().__init__(f"The token used for authentication is invalid | Token: '{token}'")
