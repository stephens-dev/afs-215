from pathlib import Path
from typing import NamedTuple, Optional


# All domain models are expected to be VALID
# Exceptions will be thrown if they're not
# ==> Ensure wherever they are created that they are indeed valid
#     -> This also mean, they can't be created outside the domain.


class DownloadableFile(NamedTuple):
    file_path: Path
    download_url: str


class KataLanguage(NamedTuple):
    name: str


class KataTemplate(NamedTuple):
    language: KataLanguage
    template_name: Optional[str]
