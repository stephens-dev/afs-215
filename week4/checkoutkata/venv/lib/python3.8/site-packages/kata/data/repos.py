import re
from pathlib import Path
from typing import List, Optional

import schema

from kata import defaults
from kata.data.io.file import FileReader, FileWriter
from kata.data.io.network import GithubApi
from kata.domain.exceptions import InvalidConfig
from kata.domain.models import KataTemplate, KataLanguage


class ConfigRepo:
    def __init__(self, config_file: Path, file_reader: FileReader, file_writer: FileWriter):
        self._file_reader = file_reader
        self._file_writer = file_writer

        self._create_config_file_with_defaults_if_doesnt_exist(config_file)
        self._load_config(config_file)
        self._validate_config()

    def get_kata_grepo_username(self) -> str:
        return self._config['KataGRepo']['User']

    def get_kata_grepo_reponame(self) -> str:
        return self._config['KataGRepo']['Repo']

    def has_template_at_root(self, language: KataLanguage) -> Optional[bool]:
        """
        :return: True if yes, False if no, None if unknown
        """
        return self._config['HasTemplateAtRoot'].get(language.name, None)

    def get_auth_token(self) -> Optional[str]:
        if 'Token' not in self._config['Auth']:
            return None
        return self._config['Auth']['Token']

    def should_skip_not_logged_in_warning(self):
        return self._config['Auth']['SkipNotLoggedInWarning']

    def _create_config_file_with_defaults_if_doesnt_exist(self, config_file):
        if not config_file.exists():
            self._file_writer.write_yaml_to_file(config_file, defaults.DEFAULT_CONFIG)

    def _load_config(self, config_file):
        self._config = self._file_reader.read_yaml(config_file)

    def _validate_config(self):
        expected_schema = schema.Schema({'KataGRepo': {'User': str,
                                                       'Repo': str},
                                         'HasTemplateAtRoot': {schema.Optional(str): bool},
                                         'Auth': {'SkipNotLoggedInWarning': bool,
                                                  schema.Optional('Token'): str}})
        try:
            expected_schema.validate(self._config)
        except schema.SchemaError as error:
            raise InvalidConfig(error)


class KataTemplateRepo:
    def __init__(self, api: GithubApi, config_repo: ConfigRepo):
        self._api = api
        self._config_repo = config_repo

    def get_for_language(self, language: KataLanguage) -> List[KataTemplate]:
        contents_of_language_root_dir = self._api.contents(self._config_repo.get_kata_grepo_username(),
                                                           self._config_repo.get_kata_grepo_reponame(),
                                                           language.name)

        if self._has_template_at_root(language, contents_of_language_root_dir):
            template_at_root = KataTemplate(language=language, template_name=None)
            return [template_at_root]

        available_template_names = self._extract_available_template_names(contents_of_language_root_dir)

        def all_kata_templates_for_language():
            for template_name in available_template_names:
                yield KataTemplate(language, template_name)

        return list(all_kata_templates_for_language())

    def _has_template_at_root(self, language, dir_contents):

        def has_template_at_root_according_to_config():
            res = self._config_repo.has_template_at_root(language)
            assert res is not None, "Shouldn't never up here"
            return res

        def config_has_an_entry_for_language():
            return self._config_repo.has_template_at_root(language) is not None

        def try_to_guess():
            def has_readme():
                for file_or_dir in dir_contents:
                    if re.match(r'^.*README(\....?)?$', file_or_dir['path']):
                        return True
                return False

            return has_readme()

        if config_has_an_entry_for_language():
            return has_template_at_root_according_to_config()
        else:
            return try_to_guess()

    @staticmethod
    def _extract_available_template_names(language_root_dir_contents):
        def extract_template_name_from_sub_path(sub_path: str):
            return sub_path.split('/')[1]

        return [extract_template_name_from_sub_path(directory['path']) for directory in language_root_dir_contents if
                directory['type'] == 'dir']


class KataLanguageRepo:
    def __init__(self, api: GithubApi, config_repo: ConfigRepo):
        self._api = api
        self._config_repo = config_repo

    def get_all(self) -> List[KataLanguage]:
        contents_of_root_dir = self._api.contents(self._config_repo.get_kata_grepo_username(),
                                                  self._config_repo.get_kata_grepo_reponame(),
                                                  '')

        return list(self._all_sub_directories_mapped_to_languages(contents_of_root_dir))

    @staticmethod
    def _all_sub_directories_mapped_to_languages(contents_of_dir):
        for file_or_dir in contents_of_dir:
            if file_or_dir['type'] == 'dir':
                sub_dir_name_interpreted_as_available_kata_language_name = file_or_dir['path']
                yield KataLanguage(name=sub_dir_name_interpreted_as_available_kata_language_name)

    def get(self, language_name: str) -> Optional[KataLanguage]:
        all_languages = self.get_all()
        for language in all_languages:
            if language.name == language_name:
                return language


class HardCoded:
    class KataTemplateRepo(KataTemplateRepo):
        def __init__(self):
            self.available_templates = {
                'java': [
                    'junit5',
                    'some-other'
                ],
                'js': [
                    'jasminesomething',
                    'maybe-mocha'
                ]
            }

        def get_for_language(self, language: KataLanguage) -> List[KataTemplate]:
            def all_for_language_or_empty():
                for template_name in self.available_templates.get(language.name, []):
                    yield KataTemplate(language, template_name)

            return list(all_for_language_or_empty())

    class KataLanguageRepo(KataLanguageRepo):
        def __init__(self):
            self.available_languages: List[str] = []

        def get_all(self) -> List[KataLanguage]:
            return [KataLanguage(lang_name) for lang_name in self.available_languages]

        def get(self, language_name: str) -> Optional[KataLanguage]:
            for available_language_name in self.available_languages:
                if available_language_name == language_name:
                    return KataLanguage(language_name)
            if language_name not in self.available_languages:
                return None

    class ConfigRepo(ConfigRepo):
        def __init__(self):
            self._config = defaults.DEFAULT_CONFIG
            self.config = self._config
