#!/usr/bin/env python3
from argparse import ArgumentDefaultsHelpFormatter
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from collections import defaultdict
import json
import logging
from lxml import etree
import re
import sys

APPLICATION_NAME = "stackoverflow_analytics"
DEFAULT_APP_HANDLER_FPATH = "stackoverflow_analytics.log"
DEFAULT_WARN_HANDLER_FPATH = "stackoverflow_analytics.warn"
DEFAULT_QUERIES_FPATH = "queries_sample.csv"
DEFAULT_QUESTIONS_FPATH = "questions_sample.xml"
DEFAULT_BIG_QUESTIONS_FPATH = "stackoverflow_posts_sample.xml"
DEFAULT_STOP_WORDS_FPATH = "stop_words_in_koi8r.txt"


logger = logging.getLogger(APPLICATION_NAME)


def load_stop_words(filepath) -> set:
    """Load stop words from file"""
    with open(filepath, "r", encoding="koi8-r") as fin:
        stop_words = set(fin.read().splitlines())
        return stop_words


def process_query(questions_filepath, stop_words, start_year, end_year, top_N):
    answer = defaultdict(int)
    with open(questions_filepath, "r", encoding="utf-8") as fin:
        content = fin.read().splitlines()
        for line in content:
            root = etree.fromstring(line, parser=etree.XMLParser())
            if int(root.get("PostTypeId")) == 1:
                score = int(root.get("Score"))
                year = int(root.get("CreationDate").split('-')[0])
                title = root.get("Title")
                title_tokens = re.findall("\w+", title.lower())
                if start_year <= year <= end_year:
                	for token in title_tokens:
                		if token not in stop_words:
                			answer[token] += score
    answer = sorted(answer.items(), key=lambda x: (-x[1], x[0]))
    answer = [list(x) for x in answer[:top_N]]
    return answer


def process_arguments(questions_filepath, stopwords_file, query_filepath):
    stop_words = load_stop_words(stopwords_file)
    with open(query_filepath, "r") as query_fin:
    	queries = query_fin.readlines()
    	for query in queries:
    		start_year, end_year, top_N = map(int, query.strip().split(','))
    		answer = process_query(questions_filepath, stop_words, start_year, end_year, top_N)
    		result = {}
    		result["start"] = start_year
    		result["end"] = end_year
    		result["top"] = answer
    		print(json.dumps(result))


def callback_parser(arguments):
    """Callback function"""
    return process_arguments(arguments.questions_filepath,
                             arguments.stopwords_file,
                             arguments.query_filepath)


def setup_parser(parser):
    """The function to setup parser arguments"""
    parser.add_argument(
        "--questions",
        default=DEFAULT_QUESTIONS_FPATH,
        dest="questions_filepath",
        help="path to questions in xml format",
    )
    parser.add_argument(
        "--stop-words",
        default=DEFAULT_STOP_WORDS_FPATH,
        dest="stopwords_file",
        help="path to stop-words file in text format",
    )
    parser.add_argument(
        "--queries",
        default=DEFAULT_QUERIES_FPATH,
        dest="query_filepath",
        help="query file in csv format to get queries for analytics",
    )
    parser.set_defaults(callback=callback_parser)


def setup_logging():
    """The function to setup logger"""
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="%(levelname)s: %(message)s",
        # datefmt="%Y-%m-%d %H:%M:%S",
    )

    app_handler = logging.FileHandler(
        filename=DEFAULT_APP_HANDLER_FPATH,
    )
    app_handler.setLevel(logging.DEBUG)
    app_handler.setFormatter(formatter)

    warn_handler = logging.FileHandler(
        filename=DEFAULT_WARN_HANDLER_FPATH,
    )
    warn_handler.setLevel(logging.WARNING)
    warn_handler.setFormatter(formatter)

    logger.addHandler(app_handler)
    logger.addHandler(warn_handler)


def main():
    """Main module function"""
    setup_logging()
    parser = ArgumentParser(
        prog="stackoverflow-analytics",
        description="A tool to query stackoverflow website.",
        formatter_class = ArgumentDefaultsHelpFormatter,
    )
    setup_parser(parser)
    arguments = parser.parse_args()
    arguments.callback(arguments)


if __name__ == "__main__":
    main()
