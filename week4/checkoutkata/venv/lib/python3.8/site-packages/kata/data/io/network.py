import requests

from kata.domain.exceptions import ApiLimitReached, InvalidAuthToken


class GithubApi:
    """
    Basic wrapper around the Github Api
    """

    def __init__(self, auth_token: str):
        self._requests = requests
        self._auth_token = auth_token

    def contents(self, user, repo, path=''):
        url = f'https://api.github.com/repos/{user}/{repo}/contents'
        if path:
            url += f'/{path}'

        response = self._get_url(url)
        return response.json()

    def download_raw_text_file(self, raw_text_file_url: str):
        response = self._get_url(raw_text_file_url)
        return response.text

    def _get_url(self, url: str):
        response = self._requests.get(url, headers=self._headers())
        self._validate_response(response)
        return response

    def _headers(self):
        if not self._auth_token:
            return {}
        return {'Authorization': f'token {self._auth_token}'}

    def _validate_response(self, response: requests.Response):
        def rate_limit_reached():
            def unauthorised():
                return response.status_code == 403

            def limit_reached():
                return int(response.headers.get('X-RateLimit-Remaining', -1)) == 0

            return unauthorised() and limit_reached()

        def invalid_auth():
            return response.status_code == 401

        if rate_limit_reached():
            raise ApiLimitReached()
        if invalid_auth():
            raise InvalidAuthToken(self._auth_token)
        response.raise_for_status()
