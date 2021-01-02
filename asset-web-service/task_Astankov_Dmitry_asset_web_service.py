#!/usr/bin/env python3
"""
Asset web service
"""
from bisect import bisect_left, insort_left
import logging.config
from lxml import html
import requests
import yaml

from flask import Flask, abort, jsonify, request, url_for


logging.config.dictConfig(yaml.safe_load("""
version: 1
formatters:
    simple:
        format: "%(levelname)s from %(name)s: %(message)s"
handlers:
    stream_handler:
        class: logging.StreamHandler
        stream: ext://sys.stderr
        level: DEBUG
        formatter: simple
    file_handler:
        class: logging.FileHandler
        filename: asset_web_service.log
        level: DEBUG
        formatter: simple
loggers:
    wiki_search_app:
        level: DEBUG
        propagate: False
        handlers:
            - file_handler
    werkzeug:
        level: DEBUG
        propagate: False
        handlers:
            - file_handler
            - stream_handler
root:
    level: DEBUG
    handlers:
        - stream_handler
"""))


DEFAULT_ENCODING = "utf-8"
CBR_DAILY_URL = "https://www.cbr.ru/eng/currency_base/daily/"
CBR_INDICATORS_URL = "https://www.cbr.ru/eng/key-indicators/"


class Asset:
    """Asset class"""
    def __init__(self, char_code: str, name: str, capital: float, interest: float):
        self.char_code = char_code
        self.name = name
        self.capital = capital
        self.interest = interest

    def __lt__(self, other):
        return self.name < other.name

    def calculate_revenue(self, period: int, currency_rate: float) -> float:
        """Calculate revenue of a given asset"""
        revenue_in_currency = self.capital * ((1.0 + self.interest) ** period - 1.0)
        revenue = revenue_in_currency * currency_rate
        return revenue

    def to_list(self) -> list:
        """Convert the asset to list"""
        return [self.char_code, self.name, self.capital, self.interest]


class Bank:
    """Bank class storing collection of assets"""
    def __init__(self, asset_collection=None):
        self.asset_collection = []
        if asset_collection:
            for asset in asset_collection:
                insort_left(self.asset_collection, asset)

    def add(self, asset: Asset):
        """Add an asset to the bank"""
        insort_left(self.asset_collection, asset)

    def contains(self, asset: Asset):
        i = bisect_left(self.asset_collection, asset)
        if i != len(self.asset_collection) and self.asset_collection[i].name == asset.name:
            return True
        return False

    def get(self, name: str):
        """Get asset by name"""
        asset = Asset("", name, 0, 0)
        i = bisect_left(self.asset_collection, asset)
        if i != len(self.asset_collection) and self.asset_collection[i].name == asset.name:
            return self.asset_collection[i].to_list()
        return []

    def clear(self):
        """Clear all assets"""
        self.asset_collection.clear()

    def calculate_revenue(self, period: int, currency_rates: dict):
        """Calculate total revenue for all assets in the bank"""
        total_revenue = sum(
            asset.calculate_revenue(period, currency_rates[asset.char_code])
            for asset in self.asset_collection
        )
        return total_revenue

    def to_list(self) -> list:
        """Convert the bask to list"""
        result = []
        for asset in self.asset_collection:
            insort_left(result, asset.to_list())
        return result


def parse_cbr_currency_base_daily(content: str):
    """The function to parse daily currency rates from CBR site"""
    root = html.fromstring(content)
    table = root.xpath('//tr')[1:]

    result = {}
    for row in table:
        result[row[1].text] = float(row[4].text) / float(row[2].text)
    return result


def parse_cbr_key_indicators(content: str):
    """
    The function to parse USD, EUR and precious metals
    rates from CBR site
    """
    root = html.fromstring(content)
    tables = root.xpath('//table')[:2]

    result = {}
    for table in tables:
        for row in table[0][1:]:
            key = row.xpath('./td/div/div/text()')[1]
            value = float(row[-1].text.replace(',', ''))
            result[key] = value
    return result


app = Flask(__name__)
app.bank = Bank()


@app.errorhandler(404)
def route_not_found(error):
    """404 error handler"""
    return "This route is not found", 404


@app.errorhandler(500)
def route_not_available(error):
    """500 error handler"""
    return "CBR service is unavailable", 503


@app.route("/cbr/daily")
def get_daily():
    """Get daily currency rates"""
    cbr_response = requests.get(CBR_DAILY_URL)
    if not cbr_response.ok:
        abort(503)

    result = parse_cbr_currency_base_daily(cbr_response.text)

    return result, 200


@app.route("/cbr/key_indicators")
def get_key_indicators():
    """Get USD, EUR and precious metals rates"""
    cbr_response = requests.get(CBR_INDICATORS_URL)
    if not cbr_response.ok:
        abort(503)

    result = parse_cbr_key_indicators(cbr_response.text)

    return result, 200


@app.route("/api/asset/add/<string:char_code>/<string:name>/<string:capital>/<string:interest>")
def api_asset_add(char_code: str, name: str, capital: str, interest: str):
    """Add an asset to the bank"""
    capital, interest = float(capital), float(interest)
    asset = Asset(char_code=char_code, name=name, capital=capital, interest=interest)

    if app.bank.contains(asset):
        return f"Asset '{name}' already exists", 403

    app.bank.add(asset)
    return f"Asset '{name}' was successfully added", 200


@app.route("/api/asset/list")
def api_asset_list():
    """Get the list of assets in the bank"""
    return jsonify(app.bank.to_list()), 200


@app.route("/api/asset/cleanup")
def api_asset_cleanup():
    """Clear all assets in the bank"""
    app.bank.clear()
    return "", 200


@app.route("/api/asset/get")
def api_asset_get():
    """Get assets with specified names from the bank"""
    names = request.args.getlist("name")

    result = []
    for name in names:
        asset = app.bank.get(name)
        if asset:
            result.append(asset)

    return jsonify(sorted(result)), 200


@app.route("/api/asset/calculate_revenue")
def api_asset_calculate_revenue():
    """
    Calculate revenue with all existing assets
    for the provided periods
    """
    periods = request.args.getlist("period")

    daily_response = requests.get(CBR_DAILY_URL)
    key_indicators_response = requests.get(CBR_INDICATORS_URL)
    currency_rates = parse_cbr_currency_base_daily(daily_response.text)
    currency_rates.update(parse_cbr_key_indicators(key_indicators_response.text))

    result = {}
    for period in periods:
        result[period] = app.bank.calculate_revenue(int(period), currency_rates)
    return result, 200
