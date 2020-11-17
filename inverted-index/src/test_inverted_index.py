from argparse import Namespace
from textwrap import dedent

import pytest

from inverted_index import InvertedIndex
from inverted_index import build_inverted_index
from inverted_index import DEFAULT_INVERTED_INDEX_SAVE_PATH
from inverted_index import callback_query, process_queries
from inverted_index import callback_build, process_build
from inverted_index import load_documents
from storage_policy import ArrayStoragePolicy

DATASET_BIG_FPATH = "../resources/wikipedia_sample"
DATASET_SMALL_FPATH = "../resources/small_wikipedia_sample"
DATASET_TINY_FPATH = "../resources/tiny_wikipedia_sample"


def test_can_load_documents_v1():
    documents = load_documents(DATASET_TINY_FPATH)
    etalon_documents = {
        123: "some words A_word and nothing",
        2: "some word B_word in this dataset",
        5: "famous_phrases to be or not to be",
        37: "all words such as A_word and B_word are here",
    }
    assert etalon_documents == documents, (
        "load_documents incorrectly loaded dataset"
    )


def test_can_load_documents_v2(tmpdir):
    dataset_str = dedent("""\
        123\tsome words A_word and nothing
        2\tsome word B_word in this dataset
        5\tfamous_phrases to be or not to be
        37\tall words such as A_word and B_word are here
    """)
    dataset_fio = tmpdir.join("tiny.dataset")
    dataset_fio.write(dataset_str)
    documents = load_documents(dataset_fio)
    etalon_documents = {
        123: "some words A_word and nothing",
        2: "some word B_word in this dataset",
        5: "famous_phrases to be or not to be",
        37: "all words such as A_word and B_word are here",
    }
    assert etalon_documents == documents, (
        "load_documents incorrectly loaded dataset"
    )


DATASET_TINY_STR = dedent("""\
    123\tsome words A_word and nothing
    2\tsome word B_word in this dataset
    5\tfamous_phrases to be or not to be
    37\tall words such as A_word and B_word are here
""")


@pytest.fixture()
def tiny_dataset_fio(tmpdir):
    dataset_fio = tmpdir.join("dataset.txt")
    dataset_fio.write(DATASET_TINY_STR)
    return dataset_fio


def test_can_load_documents(tiny_dataset_fio):
    documents = load_documents(tiny_dataset_fio)
    etalon_documents = {
        123: "some words A_word and nothing",
        2: "some word B_word in this dataset",
        5: "famous_phrases to be or not to be",
        37: "all words such as A_word and B_word are here",
    }
    assert etalon_documents == documents, (
        "load_documents incorrectly loaded dataset"
    )


@pytest.mark.parametrize(
    "query, etalon_answer",
    [
        pytest.param(["A_word"], [123, 37], id="A_word"),
        pytest.param(["B_word"], [2, 37], id="B_word"),
        pytest.param(["A_word", "B_word"], [37], id="both_words"),
        pytest.param(["word_does_not_exist"], [], id="word does not exist"),
    ],
)
def test_query_inverted_index_intersect_results(tiny_dataset_fio, query, etalon_answer):
    documents = load_documents(tiny_dataset_fio)
    tiny_inverted_index = build_inverted_index(documents)
    answer = tiny_inverted_index.query(query)
    assert sorted(answer) == sorted(etalon_answer), (
        f"Expected answer is {etalon_answer}, but you got {answer}"
    )


# @pytest.mark.skip
def test_can_load_wikipedia_sample():
    documents = load_documents(DATASET_BIG_FPATH)
    assert len(documents) == 4100, (
        "you incorrectly loaded Wikipedia sample"
    )


@pytest.fixture()
def wikipedia_documents():
    # documents = load_documents(DATASET_BIG_FPATH)
    documents = load_documents(DATASET_SMALL_FPATH)
    # documents = load_documents(DATASET_TINY_FPATH)
    return documents


@pytest.fixture()
def small_sample_wikipedia_documents():
    documents = load_documents(DATASET_SMALL_FPATH)
    return documents


# @pytest.mark.skip
def test_can_build_and_query_inverted_index(wikipedia_documents):
    wikipedia_inverted_index = build_inverted_index(wikipedia_documents)
    doc_ids = wikipedia_inverted_index.query(["wikipedia"])
    assert isinstance(doc_ids, list), "inverted index query should return list"


@pytest.fixture()
def wikipedia_inverted_index(wikipedia_documents):
    wikipedia_inverted_index = build_inverted_index(wikipedia_documents)
    return wikipedia_inverted_index


@pytest.fixture()
def small_wikipedia_inverted_index(small_sample_wikipedia_documents):
    wikipedia_inverted_index = build_inverted_index(small_sample_wikipedia_documents)
    return wikipedia_inverted_index


# @pytest.mark.skip
def test_can_dump_and_load_inverted_index(tmpdir, wikipedia_inverted_index):
    index_fio = tmpdir.join("index.dump")
    wikipedia_inverted_index.dump(index_fio)
    loaded_inverted_index = InvertedIndex.load(index_fio)
    assert wikipedia_inverted_index == loaded_inverted_index, (
        "load should return the same inverted index"
    )


# @pytest.mark.parametrize(
#     ("filepath",),
#     [
#         pytest.param(DATASET_SMALL_FPATH, id="small dataset"),
#         # pytest.param(DATASET_BIG_FPATH, marks=[pytest.mark.slow], id="big dataset"),
#     ],
# )
# @pytest.mark.skip
# def test_can_dump_and_load_inverted_index_with_array_policy_parametrized(filepath, tmpdir):
#     index_fio = tmpdir.join("index.dump")
# 
#     documents = load_documents(filepath)
#     etalon_inverted_index = build_inverted_index(documents)
# 
#     # class StoragePolicy:
#     #     @staticmethod
#     #     def dump(word_to_docs_mapping, filepath):
#     #         pass
#     #
#     #     @staticmethod
#     #     def load(filepath):#         pass
# 
#     etalon_inverted_index.dump(index_fio, storage_policy=ArrayStoragePolicy)
#     loaded_inverted_index = InvertedIndex.load(index_fio, storage_policy=ArrayStoragePolicy)
#     assert etalon_inverted_index == loaded_inverted_index, (
#         "load should return the same inverted index"
#     )


@pytest.mark.parametrize(
    "dataset_filepath",
    [
        DATASET_TINY_FPATH,
        DATASET_SMALL_FPATH,
        # pytest.param(DATASET_BIG_FPATH, marks=[pytest.mark.slow]),
    ],
)
def test_process_build_can_load_documents(dataset_filepath):
    process_build(dataset_filepath, "inverted.index")


@pytest.mark.parametrize(
    "dataset_filepath",
    [
        DATASET_TINY_FPATH,
        DATASET_SMALL_FPATH,
        # pytest.param(DATASET_BIG_FPATH, marks=[pytest.mark.slow]),
    ],
)
def test_callback_build_can_build_inverted_index_from_provided_file(dataset_filepath):
    build_arguments = Namespace(
        dataset_filepath=dataset_filepath,
        inverted_index_filepath=DEFAULT_INVERTED_INDEX_SAVE_PATH,
    )
    callback_build(build_arguments)


def test_process_queries_can_process_queries_from_provided_file(capsys):
    with open("queries-utf8.txt") as queries_fin:
        process_queries(
            inverted_index_filepath=DEFAULT_INVERTED_INDEX_SAVE_PATH,
            query_file=queries_fin,
        )
        captured = capsys.readouterr()
        assert "load inverted index" not in captured.out
        assert "load inverted index" in captured.err
        assert "two words" in captured.out
        assert "two words" not in captured.err


def test_callback_query_can_process_queries_from_provided_file():
    with open("queries-utf8.txt") as queries_fin:
        query_arguments = Namespace(
            inverted_index_filepath=DEFAULT_INVERTED_INDEX_SAVE_PATH,
            query_file=queries_fin,
        )
        callback_query(query_arguments)
