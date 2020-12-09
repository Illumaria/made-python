from contextlib import nullcontext as do_not_raise_exception
from getpass import getpass
import json
from json import JSONDecodeError
from unittest.mock import patch, MagicMock

import pytest
import requests
from requests import exceptions

DEFAULT_ENCODING = "utf-8"
DEFAULT_STATUS_CODE = 200
GITHUB_API_RESPONSE_FILEPATH = "github_api_response.txt"
GITHUB_DOCS_RESPONSE_FILEPATH = "github_docs_response.html"
URL_AUTH_TEST = "https://jigsaw.w3.org/HTTP/Basic/"
URL_GITHUB_API = "https://api.github.com"
URL_GITHUB_DOCS = "https://docs.github.com"
URL_UNKNOWN = "https://unknown.url.com"


def build_response_mock_from_content(content, encoding=DEFAULT_ENCODING, status_code=DEFAULT_STATUS_CODE):
    text = content.decode(encoding)
    response = MagicMock(
        content=content,
        encoding=encoding,
        text=text,
        status_code=status_code,
    )
    response.json.side_effect = lambda: json.loads(text)
    return response


def callback_requests_get(url):
    url_mapping = {
        URL_GITHUB_API: GITHUB_API_RESPONSE_FILEPATH,
        URL_GITHUB_DOCS: GITHUB_DOCS_RESPONSE_FILEPATH,
    }
    if url in url_mapping:
        mock_content_filepath = url_mapping[url]
        with open(mock_content_filepath , "rb") as content_fin:
            content = content_fin.read()
        mock_response = build_response_mock_from_content(content=content)
        return mock_response

    raise exceptions.ConnectionError(f"Exceeded max trial connection to {url}")


@patch("requests.get")
@pytest.mark.parametrize(
    "target_url, expected_outcome",
    [
        pytest.param(URL_GITHUB_API, do_not_raise_exception(), id="do_not_raise_exception"),
        pytest.param(URL_GITHUB_DOCS, pytest.raises(JSONDecodeError), id="raise-JSONDecodeError"),
        pytest.param(URL_UNKNOWN, pytest.raises(exceptions.ConnectionError), id="raise-ConnectionError"),
    ]
)
def test_can_mock_web(mock_requests_get, target_url, expected_outcome):
    mock_requests_get.side_effect = callback_requests_get

    with expected_outcome:
        response = requests.get(target_url)
        assert 200 == response.status_code
        assert "github" in response.text
        assert isinstance(response.json(), dict)


@pytest.mark.parametrize(
    "target_url, expected_outcome",
    [
        (URL_GITHUB_API, True),
        (URL_AUTH_TEST, False),
    ]
)
def test_http_request_is_successful(target_url, expected_outcome):
    response = requests.get(target_url)
    assert expected_outcome == bool(response)


def test_auth_website_require_correct_credentials():
    response = requests.get(URL_AUTH_TEST, auth=("user", "wrong_password"))
    assert 400 <= response.status_code < 500


@patch("test_web.getpass")
def test_auth_website_accept_correct_credentials(mock_getpass):
    mock_getpass.return_value = "guest"

    response = requests.get(URL_AUTH_TEST, auth=("guest", getpass()))
    assert True == bool(response)
