import re
from pathlib import Path
from typing import Optional, List

from kata.data.repos import KataTemplateRepo, KataLanguageRepo, ConfigRepo
from kata.domain.exceptions import InvalidKataName, KataLanguageNotFound, KataTemplateNotFound
from kata.domain.grepo import GRepo
from kata.domain.models import KataLanguage, KataTemplate


class InitKataService:
    def __init__(self, kata_language_repo: KataLanguageRepo, kata_template_repo: KataTemplateRepo, grepo: GRepo,
                 config_repo: ConfigRepo):
        self._kata_language_repo = kata_language_repo
        self._kata_template_repo = kata_template_repo
        self._config_repo = config_repo
        self._grepo = grepo

    def init_kata(self, parent_dir: Path, kata_name: str, template_language: str, template_name: Optional[str]) -> None:
        self._validate_parent_dir(parent_dir)
        self._validate_kata_name(kata_name)

        kata_template = self._get_kata_template(template_language, template_name)
        path = self._build_path(kata_template)
        files_to_download = self._grepo.get_files_to_download(user=self._config_repo.get_kata_grepo_username(),
                                                              repo=self._config_repo.get_kata_grepo_reponame(),
                                                              path=path)
        kata_dir = parent_dir / kata_name
        self._grepo.download_files_at_location(kata_dir, files_to_download)

    def list_available_languages(self) -> List[KataLanguage]:
        return self._kata_language_repo.get_all()

    def list_available_templates(self, language: str) -> List[KataTemplate]:
        kata_language = self._get_kata_language_or_raise(language)
        return self._kata_template_repo.get_for_language(kata_language)

    @staticmethod
    def _validate_parent_dir(parent_dir):
        if not parent_dir.exists():
            raise FileNotFoundError(f"Invalid Directory: '{parent_dir.absolute()}'")

    @staticmethod
    def _validate_kata_name(kata_name):
        def has_spaces():
            return len(kata_name.split(' ')) > 1

        if not kata_name:
            raise InvalidKataName(kata_name, reason='empty')
        if has_spaces():
            raise InvalidKataName(kata_name, reason='contains spaces')

        if not re.match(r'^[_a-z]*$', kata_name):
            raise InvalidKataName(kata_name)

    def _get_kata_template(self, template_language: str, template_name: str):

        def only_one_available_for_language():
            return len(templates_for_language) == 1

        def first():
            return templates_for_language[0]

        def first_found_or_raise_template_not_found():
            for template in templates_for_language:
                if template.template_name == template_name:
                    return template

            raise KataTemplateNotFound(templates_for_language)

        kata_language = self._get_kata_language_or_raise(template_language)
        templates_for_language = self._kata_template_repo.get_for_language(kata_language)

        if not template_name and only_one_available_for_language():
            return first()
        return first_found_or_raise_template_not_found()

    def _get_kata_language_or_raise(self, language_name):
        res = self._kata_language_repo.get(language_name)
        if not res:
            all_languages = self._kata_language_repo.get_all()
            raise KataLanguageNotFound(all_languages)
        return res

    @staticmethod
    def _build_path(kata_template):
        path = kata_template.language.name
        if kata_template.template_name:
            path += '/' + kata_template.template_name
        return path


class LoginService:
    def __init__(self, config_repo: ConfigRepo):
        self._config_repo = config_repo

    def is_logged_in(self) -> bool:
        return self._config_repo.get_auth_token() is not None

    def should_skip_not_logged_in_warning(self):
        return self._config_repo.should_skip_not_logged_in_warning()
