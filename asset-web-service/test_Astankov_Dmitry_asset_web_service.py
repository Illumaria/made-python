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
CBR_DAILY_RESPONSE_FILEPATH = "cbr_currency_base_daily_sample.html"
CBR_INDICATORS_RESPONSE_FILEPATH = "cbr_key_indicators_sample.html"
CBR_DAILY_URL = "https://www.cbr.ru/eng/currency_base/daily/"
CBR_INDICATORS_URL = "https://www.cbr.ru/eng/key-indicators/"
UNKNOWN_URL = "https://unknown.url.com"


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
        CBR_DAILY_URL: CBR_DAILY_RESPONSE_FILEPATH,
        CBR_INDICATORS_URL: CBR_INDICATORS_RESPONSE_FILEPATH,
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
        pytest.param(CBR_DAILY_URL, pytest.raises(JSONDecodeError), id="raise-JSONDecodeError"),
        pytest.param(CBR_INDICATORS_URL, pytest.raises(JSONDecodeError), id="raise-JSONDecodeError"),
        pytest.param(UNKNOWN_URL, pytest.raises(exceptions.ConnectionError), id="raise-ConnectionError"),
    ]
)
def test_can_mock_web(mock_requests_get, target_url, expected_outcome):
    mock_requests_get.side_effect = callback_requests_get

    with expected_outcome:
        response = requests.get(target_url)
        assert 200 == response.status_code
        assert "Dollar" in response.text
        assert isinstance(response.json(), dict)


@pytest.mark.parametrize(
    "target_url, expected_outcome",
    [
        (CBR_DAILY_URL, True),
        (CBR_INDICATORS_URL, True),
    ]
)
def test_http_request_is_successful(target_url, expected_outcome):
    response = requests.get(target_url)
    assert expected_outcome == bool(response)
