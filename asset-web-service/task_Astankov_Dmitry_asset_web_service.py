#!/usr/bin/env python3
import json
import logging.config
from lxml import html
import requests
import yaml

from flask import Flask, abort, jsonify


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
DEFAULT_STATUS_CODE = 200
CBR_DAILY_URL = "https://www.cbr.ru/eng/currency_base/daily/"
CBR_INDICATORS_URL = "https://www.cbr.ru/eng/key-indicators/"


class Asset:
    def __init__(self, char_code: str, name: str, capital: float, interest: float):
        self.char_code = char_code
        self.name = name
        self.capital = capital
        self.interest = interest

    def calculate_revenue(self, years: int) -> float:
        revenue = self.capital * ((1.0 + self.interest) ** years - 1.0)
        return revenue

    def to_json(self):
        return json.dumps([self.char_code, self.name, self.capital, self.interest])


class Bank:
    def __init__(self):
        self.asset_collection = {}

    def add(self, char_code: str, name: str, capital: float, interest: float):
        asset = Asset(char_code, name, capital, interest)
        self.asset_collection[asset.char_code] = asset

    def to_json(self):
        return json.dumps([x.to_json() for x in self.asset_collection.values()])


bank = Bank()
app = Flask(__name__)


def parse_cbr_currency_web_daily(content: str):
    root = html.fromstring(content)
    table = root.xpath('//tr')[1:]

    result = {}
    for row in table:
        result[row[1].text] = float(row[4].text) / float(row[2].text)
    return result


def parse_cbr_key_indicators(content: str):
    root = html.fromstring(content)
    tables = root.xpath('//table')[:2]

    result = {}
    for table in tables:
        for row in table[0][1:]:
            key = row.xpath('./td/div/div/text()')[1]
            value = float(row[-1].text.replace(',', ''))
            result[key] = value
    return result


@app.route("/cbr/daily/")
def get_daily():
    cbr_response = requests.get(CBR_DAILY_URL)
    if not cbr_response.ok:
        abort(503)

    result = parse_cbr_currency_web_daily(cbr_response.text)

    return result


@app.route("/cbr/key_indicators/")
def get_key_indicators():
    cbr_response = requests.get(CBR_INDICATORS_URL)
    if not cbr_response.ok:
        abort(503)

    result = parse_cbr_key_indicators(cbr_response.text)

    return result


@app.route("/api/asset/add/<string:char_code>/<string:name>/<float:capital>/<float:interest>/")
def api_asset_add(char_code: str, name: str, capital: float, interest: float):
    if char_code in bank.asset_collection:
        return f"Asset '{name}' already exists", 403

    bank.add(char_code=char_code, name=name, capital=capital, interest=interest)
    return f"Asset '{name}' was successfully added", 200


@app.route("/api/asset/list/")
def api_asset_list():
    # return jsonify(list(bank.asset_collection.values())), 200
    return bank.to_json(), 200


@app.errorhandler(404)
def route_not_found():
    return "This route is not found", 404


@app.errorhandler(503)
def route_not_available():
    return "CBR service is unavailable", 503
