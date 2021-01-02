from contextlib import nullcontext as do_not_raise_exception
import json
from json import JSONDecodeError
from collections import namedtuple
from unittest.mock import patch, MagicMock

import pytest
import requests
from requests import exceptions

from task_Astankov_Dmitry_asset_web_service import (
    app,
    parse_cbr_currency_base_daily,
    parse_cbr_key_indicators,
    Asset,
    Bank,
    CBR_DAILY_URL,
    CBR_INDICATORS_URL,
    DEFAULT_ENCODING,
)

CBR_DAILY_RESPONSE_FILEPATH = "cbr_currency_base_daily_sample.html"
CBR_INDICATORS_RESPONSE_FILEPATH = "cbr_key_indicators_sample.html"
DEFAULT_STATUS_CODE = 200
UNKNOWN_URL = "https://unknown.url.com"


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_service_does_not_reply_to_nonexistent_path(client):
    expected_message = "This route is not found"
    response = client.get("/")
    status_code = response.status_code
    message = response.data.decode(encoding=DEFAULT_ENCODING)
    assert 404 == status_code, (
        f"Wrong status code: expected 404, got {status_code}"
    )
    assert expected_message == message, (
        f"Wrong message: expected {expected_message}, got {message}"
    )


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



def test_asset_init():
    asset = Asset("EUR", "euros", 100, 0.1)

    assert asset.name == "euros" and \
           asset.capital == 100.0 and \
           asset.interest == 0.1, ("Failed to create asset")


@pytest.mark.parametrize(
    "period, rate, expected_result",
    [
        pytest.param(1, 77.0, 100 * (1.1 ** 1 - 1.0) * 77.0),
        pytest.param(3, 85.0, 100 * (1.1 ** 3 - 1.0) * 85.0),
        pytest.param(7, 82.0, 100 * (1.1 ** 7 - 1.0) * 82.0),
    ]
)
def test_can_calculate_asset_revenue_correclty(period, rate, expected_result):
    asset = Asset("EUR", "euros", 100, 0.1)
    result = asset.calculate_revenue(period, rate)
    assert expected_result == result, (
        f"Wrong revenue value: expected {expected_result:.3f}, got {result:.3f}"
    )


@pytest.mark.parametrize(
    "left_asset, right_asset, expected_result",
    [
        pytest.param(Asset("USD", "dollars", 100, 0.1), Asset("EUR", "euros", 50, 0.2), True),
        pytest.param(Asset("EUR", "euros", 50, 0.2), Asset("USD", "dollars", 100, 0.1), False),
    ]
)
def test_can_compare_assets_correctly(left_asset, right_asset, expected_result):
    result = left_asset < right_asset
    assert result is expected_result, (
        f"Wrong comparison: expected {expected_result} for assets with names \
        {left_asset.name} and {right_asset.name}, got {result}"
    )


def test_can_add_assets_to_bank():
    asset = Asset("EUR", "euros", 50, 0.2)
    init_asset_1 = Asset("USD", "dollars", 100, 0.1)
    init_asset_2 = Asset("JPY", "yens", 1000, 0.05)

    bank = Bank([init_asset_1, init_asset_2])
    bank.add(asset)
    result = [x.name for x in bank.asset_collection]

    expected_result = sorted(["euros", "dollars", "yens"])
    assert expected_result == result, (
        f"Wrong result: expected {expected_result}, got {result}"
    )


@pytest.mark.parametrize(
    "asset, expected_result",
    [
        pytest.param(Asset("EUR", "euros", 50, 0.2), True),
        pytest.param(Asset("USD", "dollars", 100, 0.1), False),
    ]
)
def test_bank_contains_works_correctly(asset, expected_result):
    asset_1 = Asset("EUR", "euros", 50, 0.2)
    asset_2 = Asset("JPY", "yens", 1000, 0.05)
    bank = Bank([asset_1, asset_2])
    result = bank.contains(asset)
    assert expected_result == result, (
        f"Wrong result: expected {expected_result}, got {result}"
    )


def test_bank_clear_works_correctly():
    asset_1 = Asset("EUR", "euros", 50, 0.2)
    asset_2 = Asset("JPY", "yens", 1000, 0.05)
    bank = Bank([asset_1, asset_2])
    bank.clear()
    assert len(bank.asset_collection) == 0, (
        f"Wrong result: expected 0, got {len(bank.asset_collection)}"
    )


def test_bank_get_works_correctly():
    asset_1 = Asset("EUR", "euros", 50, 0.2)
    asset_2 = Asset("JPY", "yens", 1000, 0.05)
    bank = Bank([asset_1, asset_2])
    result = bank.get("yens")
    expected_result = ["JPY", "yens", 1000, 0.05]
    assert expected_result == result, (
        f"Wrong result: expected {expected_result}, got {result}"
    )


def test_bank_to_list_is_sorted_and_works_correctly():
    asset_1 = Asset("JPY", "ayens", 1000, 0.05)
    asset_2 = Asset("EUR", "euros", 50, 0.2)
    bank = Bank([asset_1, asset_2])

    expected_result = [
        ["EUR", "euros", 50, 0.2],
        ["JPY", "ayens", 1000, 0.05],
    ]
    result = bank.to_list()
    assert expected_result == result, (
        f"Wrong result: expected {expected_result}, got {result}"
    )




def test_bank_calculate_revenue_works_correctly():
    assets = [
        Asset("EUR", "euros", 50, 0.2),
        Asset("JPY", "yens", 1000, 0.05),
        Asset("USD", "dollars", 100, 0.1),
    ]
    key_indicators = {
        "EUR": 90.8,
        "USD": 73.9,
    }
    currency_rates = {
        "JPY": 0.716,
    }
    currency_rates.update(key_indicators)
    assert 3 == len(currency_rates)
    period = 4
    expected_result = sum(
        asset.calculate_revenue(period, currency_rates[asset.char_code])
        for asset in assets
    )
    bank = Bank(assets)
    result = bank.calculate_revenue(period, currency_rates)
    assert expected_result == result, (
        f"Wrong result: expected {expected_result}, got {result}"
    )


def test_parse_cbr_currency_base_daily_works_correctly():
    expected_result = {
        "AUD": 57.0229,
        "AZN": 44.4127,
        "AMD": 0.144485
    }
    with open(CBR_DAILY_RESPONSE_FILEPATH, "r", encoding=DEFAULT_ENCODING) as fin:
        content = fin.read()
    result = parse_cbr_currency_base_daily(content)
    for key in expected_result:
        assert key in result, (
            f"Wrong result: key {key} is absent from result {result}"
        )
        assert result[key] == expected_result[key], (
            f"Wrong result: expected {expected_result[key]}, got {result[key]}"
        )


def test_parse_cbr_key_indicators_works_correctly():
    expected_result = {
        "USD": 75.4571,
        "EUR": 91.9822,
        "Au": 4529.59,
        "Ag": 62.52,
        "Pt": 2459.96,
        "Pd": 5667.14
    }
    with open(CBR_INDICATORS_RESPONSE_FILEPATH, "r", encoding=DEFAULT_ENCODING) as fin:
        content = fin.read()
    result = parse_cbr_key_indicators(content)
    for key in expected_result:
        assert key in result, (
            f"Wrong result: key {key} is absent from result {result}"
        )
        assert result[key] == expected_result[key], (
            f"Wrong result: expected {expected_result[key]}, got {result[key]}"
        )


@patch("requests.get")
def test_cbr_daily_page_unavailable(mock_get, client):
    mock_get.return_value.status_code = 503
    expected_message = "CBR service is unavailable"
    result = client.get("/cbr/daily", follow_redirects=True)
    message = result.data.decode(encoding=DEFAULT_ENCODING)
    assert mock_get.called_once(CBR_DAILY_URL)
    assert 503 == result.status_code, (
        f"Wrong status code: expected 503, got {result.status_code}"
    )
    assert expected_message == message, (
        f"Wrong message: expected {expected_message}, got {message}"
    )


@pytest.mark.parametrize(
    "route",
    [
        pytest.param("/api/asset/add/JPY/yens/1000/0.05"),
        pytest.param("/api/asset/add/EUR/euros/50/0.2"),
    ]
)
def test_api_add_asset_works_correctly(route, client):
    response = client.get(route, follow_redirects=True)
    message = response.data.decode(encoding=DEFAULT_ENCODING)
    asset_name = client.application.bank.asset_collection[0].name
    expected_message = f"Asset '{asset_name}' was successfully added"
    assert 200 == response.status_code, (
        f"Wrong status code: expected 200, got {response.status_code}"
    )
    assert expected_message == message, (
        f"Wrong message: expected {expected_message}, got {message}"
    )


def test_api_asset_cleanup_works_correctly(client):
    client.get("/api/asset/add/JPY/yens/1000/0.05", follow_redirects=True)
    response = client.get("/api/asset/cleanup", follow_redirects=True)
    message = response.data.decode(encoding=DEFAULT_ENCODING)
    assert 200 == response.status_code, (
        f"Wrong status code: expected 200, got {response.status_code}"
    )
    assert "" == message, (
        f"Wrong message: expected empty message, got {message}"
    )
    size = len(client.application.bank.asset_collection)
    assert 0 == size, (
        f"Cleanup failed: expected size of 0, got {size}"
    )


def test_api_asset_list_works_correctly(client):
    client.application.bank = Bank([
        Asset("EUR", "euros", 50, 0.2),
        Asset("JPY", "yens", 1000, 0.05),
        Asset("USD", "dollars", 100, 0.1),
    ])
    expected_result = [
        ["EUR", "euros", 50, 0.2],
        ["JPY", "yens", 1000, 0.05],
        ["USD", "dollars", 100, 0.1],
    ]
    response = client.get("/api/asset/list", follow_redirects=True)
    assert response.status_code == 200, (
        f"Wrong status code: expected 200, got {response.status_code}"
    )
    assert response.json == expected_result, (
        f"Wrong result: expected {expected_result}, got {response.json}"
    )


@pytest.mark.parametrize(
    "route, expected_result",
    [
        pytest.param(
            "/api/asset/get?name=yens&name=dollars",
            [
                ["JPY", "yens", 1000, 0.05],
                ["USD", "dollars", 100, 0.1],
            ]
        ),
        pytest.param(
            "/api/asset/get?name=euros",
            [
                ["EUR", "euros", 50, 0.2],
            ]
        ),
    ]
)
def test_api_asset_get_works_correctly(route, expected_result, client):
    client.application.bank = Bank([
        Asset("EUR", "euros", 50, 0.2),
        Asset("JPY", "yens", 1000, 0.05),
        Asset("USD", "dollars", 100, 0.1),
    ])
    response = client.get(route)
    assert 200 == response.status_code, (
        f"Wrong status code: expected 200, got {response.status_code}"
    )
    assert expected_result == response.json, (
        f"Wrong result: expected {expected_result}, got {response.json}"
    )


@patch("requests.get")
@pytest.mark.parametrize(
    "route, periods",
    [
        pytest.param("/api/asset/calculate_revenue?period=2", ["2"]),
        pytest.param("/api/asset/calculate_revenue?period=3&period=7", ["3", "7"]),
    ]
)
def test_api_calculate_revenue_works_correctly(mock_get, route, periods, client):
    side_effect = []
    return_value = namedtuple("return_value", ["text", "status_code"])
    with open(CBR_DAILY_RESPONSE_FILEPATH, "r", encoding=DEFAULT_ENCODING) as fin:
        side_effect.append(return_value(fin.read(), 200))
    with open(CBR_INDICATORS_RESPONSE_FILEPATH, "r", encoding=DEFAULT_ENCODING) as fin:
        side_effect.append(return_value(fin.read(), 200))
    mock_get.side_effect = side_effect
    currency_rates = {
        "AUD": 57.0229,
        "AZN": 44.4127,
        "JPY": 0.729265,
        "AMD": 0.144485,
    }
    key_indicators = {
        "USD": 75.4571,
        "EUR": 91.9822,
        "Au": 4529.59,
        "Ag": 62.52,
        "Pt": 2459.96,
        "Pd": 5667.14,
    }
    currency_rates.update(key_indicators)
    client.application.bank = Bank([
        Asset("EUR", "euros", 50, 0.2),
        Asset("Pt", "platinum", 120, 0.03),
        Asset("JPY", "yens", 1000, 0.05),
        Asset("USD", "dollars", 100, 0.1),
    ])
    expected_result = {}
    for period in periods:
        expected_result[period] = \
            client.application.bank.calculate_revenue(int(period), currency_rates)
    response = client.get(route)
    assert mock_get.called_once(CBR_DAILY_URL)
    assert mock_get.called_once(CBR_INDICATORS_URL)
    assert expected_result == response.json, (
        f"Wrong result: expected {expected_result}, got {response.json}"
    )
    assert 200 == response.status_code, (
        f"Wrong status code: expected 200, got {response.status_code}"
    )
