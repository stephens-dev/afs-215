from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pprint import pprint
from textwrap import dedent
from typing import List

import click

from kata.data.io.file import FileWriter, FileReader
from kata.data.io.network import GithubApi
from kata.data.repos import KataTemplateRepo, KataLanguageRepo, ConfigRepo
from kata.domain.exceptions import KataError, KataLanguageNotFound, KataTemplateNotFound
from kata.domain.grepo import GRepo
from kata.domain.models import DownloadableFile
from kata.domain.services import InitKataService, LoginService

SANDBOX = Path('./sandbox')


@click.group()
@click.pass_context
def cli(ctx: click.Context):
    config_file_path_as_string = '~/.katacli'
    config_file = Path(config_file_path_as_string).expanduser()
    if not config_file.exists():
        print_warning('Config file was not found!')
        print_warning('')
        print_warning('A new config file will be created and loaded with default settings.')
        print_warning(f"Config file location: '{config_file_path_as_string}'")
        print_warning('')
    try:
        main = KataMainContext(config_file)
        ctx.obj = main
        print_warning_if_not_auth(main)
    except KataError as error:
        print_error(str(error))
        exit(1)


@cli.command()
@click.pass_context
@click.argument('kata_name')
@click.argument('template_language')
@click.argument('template_name', required=False)
def init(ctx: click.Context, kata_name, template_language, template_name):
    main_ctx: KataMainContext = ctx.obj

    current_dir = Path('.')
    print_normal(f"Initializing Kata in './{kata_name}'")
    print_normal(f"  - Kata Language: '{template_language}'")
    print_normal(f"  - Kata Template: '{template_name}'")
    print_normal("")
    try:
        main_ctx.init_kata_service.init_kata(current_dir, kata_name, template_language, template_name)
        print_success('Done!')

    except KataLanguageNotFound as lang_not_found:
        print_error(f"Language '{template_language}' could not be found!")
        print_error('')
        print_error('Available languages:')
        for lang in lang_not_found.available_languages:
            print_error(f"  - {lang.name}")

    except KataTemplateNotFound as template_not_found:
        def has_only_root_template():
            return len(template_not_found.available_templates) == 1 \
                   and template_not_found.available_templates[0].template_name is None

        print_error(f"Template '{template_name}' could not be found!")
        print_error('')

        if has_only_root_template():
            print_warning(f"Language '{template_language}' only has one template, and its located at its root")
            print_warning(f"To initialize a kata with '{template_language}', simply do not specify any template name:")
            print_warning('')
            print_warning(f"    kata init {kata_name} {template_language}")
            print_warning('')
        else:
            print_error(f"Available templates for '{template_language}':")
            for template in template_not_found.available_templates:
                print_error(f"  - {template.template_name}")

    except KataError as error:
        print_error(str(error))


@cli.group()
@click.pass_context
def list(_ctx: click.Context):
    pass


@list.command()
@click.pass_context
def languages(ctx: click.Context):
    main_ctx: KataMainContext = ctx.obj
    try:
        available_kata_languages = main_ctx.init_kata_service.list_available_languages()
        print_normal("Available languages:")
        for lang in available_kata_languages:
            print_normal(f"  - '{lang.name}''")

    except KataError as error:
        print_error(str(error))


@list.command()
@click.pass_context
@click.argument('language')
def templates(ctx: click.Context, language):
    main_ctx: KataMainContext = ctx.obj
    try:
        available_kata_templates = main_ctx.init_kata_service.list_available_templates(language)
        print_normal(f"Available templates for '{language}':")
        for template in available_kata_templates:
            print_normal(f"  - '{template.template_name}'")

    except KataLanguageNotFound as lang_not_found:
        print_error(f"Language '{language}' could not be found!")
        print_error('')
        print_error('Available languages:')
        for lang in lang_not_found.available_languages:
            print_error(f"  - {lang.name}")

    except KataError as error:
        print_error(str(error))


@cli.group()
@click.pass_context
def debug(_ctx: click.Context):
    pass


@debug.command()
@click.argument('github_user')
@click.argument('repo')
@click.argument('sub_path_in_repo', default='')
@click.pass_context
def explore(ctx: click.Context, github_user, repo, sub_path_in_repo):
    main_ctx: KataMainContext = ctx.obj
    click.echo('Debug - Print all files in repo')
    click.echo('')
    click.echo('Exploring:')
    click.echo(f" - User: '{github_user}'")
    click.echo(f" - Repo: '{repo}'")
    click.echo(f" - SubPath in Repo: '{sub_path_in_repo}'")
    click.echo('')
    result = main_ctx.grepo.get_files_to_download(github_user, repo, sub_path_in_repo)
    pprint(result)
    click.echo('')
    click.echo('Done')


@debug.command()
@click.argument('github_user')
@click.argument('repo')
@click.argument('sub_path_in_repo', default='')
@click.pass_context
def download(ctx: click.Context, github_user, repo, sub_path_in_repo):
    if not SANDBOX.exists():
        raise KataError("Please create an empty './sandbox' directory before proceeding")
    for _ in SANDBOX.iterdir():
        raise KataError("Please create an EMPTY './sandbox' directory before proceeding")

    main_ctx: KataMainContext = ctx.obj
    click.echo(f'Sandbox: {SANDBOX.absolute()}')

    repo_files: List[DownloadableFile] = main_ctx.grepo.get_files_to_download(github_user, repo, sub_path_in_repo)
    click.echo('Finished fetching the list. Writing to drive now')
    main_ctx.grepo.download_files_at_location(SANDBOX, repo_files)
    click.echo('Done! (probably ^_^)')


@debug.command()
def debug():
    p = Path('~/.katacli').expanduser()
    print_normal(p.absolute())


class KataMainContext:
    file_reader: FileReader
    file_writer: FileWriter
    api: GithubApi
    executor: ThreadPoolExecutor

    config_repo: ConfigRepo
    kata_template_repo: KataTemplateRepo
    kata_language_repo: KataLanguageRepo

    grepo: GRepo
    init_kata_service: InitKataService
    login_service: LoginService

    def __init__(self, config_file):
        self.config_file = config_file

        def init_base_deps():
            self.executor = ThreadPoolExecutor(100)
            self.file_writer = FileWriter()
            self.file_reader = FileReader()

        def init_config():
            self.config_repo = ConfigRepo(self.config_file, self.file_reader, self.file_writer)

        def init_network():
            auth_token = self.config_repo.get_auth_token()
            self.api = GithubApi(auth_token)

        def init_repos():
            self.kata_template_repo = KataTemplateRepo(self.api, self.config_repo)
            self.kata_language_repo = KataLanguageRepo(self.api, self.config_repo)

        def init_domain():
            self.grepo = GRepo(self.api, self.file_writer, self.executor)
            self.init_kata_service = InitKataService(self.kata_language_repo,
                                                     self.kata_template_repo,
                                                     self.grepo,
                                                     self.config_repo)
            self.login_service = LoginService(self.config_repo)

        init_base_deps()
        init_config()
        init_network()
        init_repos()
        init_domain()


def print_error(msg):
    click.secho(msg, fg='red')


def print_success(msg):
    click.secho(msg, fg='green')


def print_warning(msg):
    click.secho(msg, fg='yellow')


def print_normal(msg):
    click.echo(msg)


def print_warning_if_not_auth(main_context: KataMainContext):
    if main_context.login_service.is_logged_in():
        return
    if main_context.login_service.should_skip_not_logged_in_warning():
        return

    print_warning(dedent("""\
    You are not logged-in!
    
    There is a rate-limit of 60 calls per hours on the Github API for un-authenticated requests.
    
    The 'kata' tool will work just fine if listing a couple of language or initializing
    one or 2 kata on a private connection. But if you're experimenting around the rate limit 
    will be quickly reached.
    
    Also, for un-authenticated requests the rate limit is shared across all users of the network,
    the limiting is based on the public IP. For that reason, when using the tool in SoCraTes 
    conferences, authentication is required.
    
    To skip this warning, set the following option to 'True' in the config:
        
        Auth:
          SkipNotLoggedInWarning: True
          
    More information about login are available in the README.
    """))
