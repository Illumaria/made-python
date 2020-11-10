#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from collections import defaultdict
import re
import struct

DEFAULT_DATASET_PATH = "../resources/wikipedia_sample"
DEFAULT_INVERTED_INDEX_SAVE_PATH = "inverted.index"
DEFAULT_STOPWORDS_PATH = "../resources/stop_words_en.txt"


class InvertedIndex:
    def __init__(self, documents: dict):
        self.inverted_index = documents

    def __eq__(self, other):
        return self.inverted_index == other.inverted_index

    def query(self, words: list) -> list:
        """Return the list of relevant documents for the given query"""
        assert isinstance(words, list), (
            "query should be provided with a list of words, but user provided: "
            f"{repr(words)}"
        )
        result = set()
        for word in words:
            if len(result) == 0:
                result.update(self.inverted_index[word.lower()])
            else:
                result = result & set(self.inverted_index[word.lower()])
        return list(result)

    def dump(self, filepath: str):
        with open(filepath, "wb") as fout:
            fout.write(struct.pack("I", len(self.inverted_index)))
            for key, vals in self.inverted_index.items():
                key = bytes(key, 'utf-8')
                fout.write(struct.pack(f"I{len(key)}s", len(key), key))
                fout.write(struct.pack("I", len(vals)))
                for val in vals:
                    fout.write(struct.pack("I", val))

    @classmethod
    def load(cls, filepath: str):
        with open(filepath, "rb") as fin:
            encoding = 'utf-8'
            data = fin.read()
            (index_len,), data = struct.unpack("I", data[:4]), data[4:]
            inverted_index = defaultdict(list)

            for _ in range(index_len):
                (key_len,), data = struct.unpack("I", data[:4]), data[4:]
                key, data = data[:key_len].decode(encoding), data[key_len:]
                (vals_num,), data = struct.unpack("I", data[:4]), data[4:]
                for _ in range(vals_num):
                    (val,), data = struct.unpack("I", data[:4]), data[4:]
                    inverted_index[key].append(val)

            inverted_index = InvertedIndex(inverted_index)
            return inverted_index


def load_documents(filepath: str) -> dict:
    """Load documents to build inverted index"""
    result = {}
    with open(filepath, "r") as fin:
        for line in fin:
            line = line.strip().split(sep='\t')
            result[int(line[0])] = line[1]
    return result


def load_stop_words(filepath: str) -> str:
    """Load stop words from file"""
    with open(filepath, "r") as fin:
        return fin.read().strip()


def build_inverted_index(documents: dict) -> InvertedIndex:
    """Build inverted index for provided documents"""
    inverted_index = defaultdict(list)
    stop_words = load_stop_words(DEFAULT_STOPWORDS_PATH)
    for i, document in documents.items():
        document = re.sub(r"\W+", " ", document)
        for term in document.lower().split():
            if (re.search(term, stop_words) is None) and (i not in inverted_index[term]):
                inverted_index[term].append(i)
    inverted_index = InvertedIndex(inverted_index)
    return inverted_index


def callback_build(arguments):
    pass


def callback_query(arguments):
    pass


def setup_parser(parser):
    subparsers = parser.add_subparsers(help="choose command")

    build_parser = subparsers.add_parser(
        "build",
        help="build inverted index and save result in binary format on disk",
        formatter_class = ArgumentDefaultsHelpFormatter,
    )

    build_parser.add_argument(
        "-d", "--dataset",
        default=DEFAULT_DATASET_PATH,
        help="path to dataset to load, default path is %(default)s",
    )
    build_parser.add_argument(
        "-o", "--output",
        default=DEFAULT_INVERTED_INDEX_SAVE_PATH,
        help="path to store inverted index in binary format",
    )
    build_parser.set_defaults(callback=callback_build)

    query_parser = subparsers.add_parser(
        "query",
        help="query inverted index",
        formatter_class = ArgumentDefaultsHelpFormatter,
    )
    query_parser.add_argument(
        "-i", "--input",
        default=DEFAULT_INVERTED_INDEX_SAVE_PATH,
        help="path to read inverted index in binary format",
    )
    query_parser.add_argument(
        "-q", "--query",
        metavar="WORD",
        nargs="+",
        required=True,
        help="query to run against inverted index",
    )
    query_parser.set_defaults(callback=callback_query)


def process_arguments(dataset_filepath: str, query: list) -> list:
    documents = load_documents(dataset_filepath)
    inverted_index = build_inverted_index(documents)
    # inverted_index.dump(path)
    # inverted_index = InvertedIndex.load(path)
    document_ids = inverted_index.query(query)
    return document_ids


def main():
    parser = ArgumentParser(
        prog="inverted-index",
        description="A tool to build, dump, load, and query inverted index.",
        formatter_class = ArgumentDefaultsHelpFormatter,
    )
    setup_parser(parser)
    arguments = parser.parse_args()
    print(arguments)

    arguments.callback(arguments)
    
    # documents = load_documents("../resources/tiny_wikipedia_sample")
    # stop_words = load_stop_words("../resources/stop_words_en.txt")
    # path = "../resources/tiny_dump_3"
    # inverted_index.dump(path)
    # inverted_index = InvertedIndex.load(path)
    # print(inverted_index.inverted_index)
    # document_ids = inverted_index.query(["two", "words"])


if __name__ == "__main__":
    main()
