#!/usr/bin/env python3

"""
Stackoverflow Analytics module provides functionality
to query stackoverflow questions data.
"""

from argparse import ArgumentDefaultsHelpFormatter
from argparse import ArgumentParser
from collections import defaultdict
import json
import logging
import re

from lxml import etree


APPLICATION_NAME = "stackoverflow_analytics"
DEFAULT_APP_HANDLER_FPATH = "stackoverflow_analytics.log"
DEFAULT_WARN_HANDLER_FPATH = "stackoverflow_analytics.warn"
DEFAULT_QUERIES_FPATH = "queries_sample.csv"
DEFAULT_QUESTIONS_FPATH = "questions_sample.xml"
DEFAULT_STOP_WORDS_FPATH = "stop_words_in_koi8r.txt"


logger = logging.getLogger(APPLICATION_NAME)


def load_stop_words(stopwords_filepath: str) -> set:
    """Load stop words from file"""
    with open(stopwords_filepath, "r", encoding="koi8-r") as fin:
        stop_words = set(fin.read().splitlines())
        return stop_words


def build_dataset(questions_filepath: str, stop_words: set) -> dict:
    """The function to build dataset from questions file"""
    dataset = defaultdict(list)
    with open(questions_filepath, "r", encoding="utf-8") as fin:
        content = fin.read().splitlines()
        for line in content:
            root = etree.fromstring(line, parser=etree.XMLParser())
            if int(root.get("PostTypeId")) == 1:
                score = int(root.get("Score"))
                year = int(root.get("CreationDate").split('-')[0])
                title = root.get("Title")
                title_tokens = re.findall(r"\w+", title.lower())
                for token in set(title_tokens):
                    if token not in stop_words:
                        dataset[token].append((year, score))
    return dataset


def process_query(query: str, dataset: dict) -> dict:
    """The function to process a single query"""
    start_year, end_year, top_n = map(int, query.strip().split(','))
    logger.debug('got query "%s,%s,%s"', start_year, end_year, top_n)
    answer = defaultdict(int)
    for key, values in dataset.items():
        for value in values:
            if start_year <= value[0] <= end_year:
                answer[key] += value[1]

    answer = sorted(answer.items(), key=lambda x: (-x[1], x[0]))
    if len(answer) < top_n:
        logger.warning(
            'not enough data to answer, found %s words out of %s for period "%s,%s"',
            len(answer), top_n, start_year, end_year
        )
    answer = [list(x) for x in answer[:top_n]]
    answer = {"start": start_year, "end": end_year, "top": answer}
    return answer


def process_queries(query_filepath, dataset):
    """The function to process queries in the given file"""
    with open(query_filepath, "r") as query_fin:
        queries = query_fin.read().splitlines()
        for query in queries:
            answer = process_query(query, dataset)
            print(json.dumps(answer))


def process_arguments(questions_filepath, stopwords_filepath, query_filepath):
    """The function to process command-line arguments"""
    stop_words = load_stop_words(stopwords_filepath)
    dataset = build_dataset(questions_filepath, stop_words)
    logger.info("process XML dataset, ready to serve queries")
    process_queries(query_filepath, dataset)
    logger.info("finish processing queries")


def callback_parser(arguments):
    """Callback function"""
    return process_arguments(arguments.questions_filepath,
                             arguments.stopwords_filepath,
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
        dest="stopwords_filepath",
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
