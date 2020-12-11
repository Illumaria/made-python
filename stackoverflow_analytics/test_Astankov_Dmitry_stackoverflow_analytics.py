from argparse import Namespace
import pytest
# from unittest.mock import call, patch, MagicMock

from task_Astankov_Dmitry_stackoverflow_analytics import (
    load_stop_words,
    build_dataset,
    process_query,
    process_queries,
    process_arguments,
    callback_parser,
)


DEFAULT_STOP_WORDS_FPATH = "stop_words_sample.txt"
DEFAULT_QUESTIONS_FPATH = "questions_sample.xml"
DEFAULT_QUERIES_FPATH = "queries_sample.csv"


def test_can_open_xml_file():
    with open(DEFAULT_QUESTIONS_FPATH, "r") as questions_fin:
        content = questions_fin.read()
        assert "What is SEO" in content


def test_load_stop_words_returns_correct_value_type():
    stop_words = load_stop_words(DEFAULT_STOP_WORDS_FPATH)
    assert isinstance(stop_words, set)


@pytest.fixture()
def stop_words():
    result = load_stop_words(DEFAULT_STOP_WORDS_FPATH)
    return result


def test_can_build_dataset_from_xml_file(stop_words):
    dataset = build_dataset(DEFAULT_QUESTIONS_FPATH, stop_words)
    assert 8 == len(dataset)


@pytest.fixture()
def dataset(stop_words):
    result = build_dataset(DEFAULT_QUESTIONS_FPATH, stop_words)
    return result


@pytest.mark.parametrize(
    "query",
    [
        ("2019,2019,2"),
        ("2019,2020,4"),
        ("2010,2012,4"),
    ]
)
def test_can_process_query(query, dataset):
    result = process_query(query, dataset)
    assert isinstance(result, dict)


def test_can_process_queries_from_file(dataset):
    process_queries(DEFAULT_QUERIES_FPATH, dataset)


def test_callback_parser():
    arguments = Namespace(
        questions_filepath=DEFAULT_QUESTIONS_FPATH,
        stopwords_filepath=DEFAULT_STOP_WORDS_FPATH,
        query_filepath=DEFAULT_QUERIES_FPATH,
    )
    print(arguments)
    callback_parser(arguments)
