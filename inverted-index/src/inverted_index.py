#!/usr/bin/env python3

"""
InvertedIndex class provides functionality
to build and query inverted index.

Use load_documents to load a file into memory.
Use build_inverted_index to construct an InvertedIndex object.
"""

from argparse import ArgumentDefaultsHelpFormatter
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from argparse import FileType
from collections import defaultdict
from io import TextIOWrapper
# import re
import struct
import sys

DEFAULT_DATASET_PATH = "../resources/wikipedia_sample"
DEFAULT_INVERTED_INDEX_SAVE_PATH = "inverted.index"
DEFAULT_STOPWORDS_PATH = "../resources/stop_words_en.txt"


class EncodedFileType(FileType):
    """FileType extension for stdin/stdout with encoding"""
    def __call__(self, string):
        """Overrided __call__ method of the FileType class"""
        # the special argument "-" means sys.std{in,out}
        if string == '-':
            if 'r' in self._mode:
                stdin = TextIOWrapper(sys.stdin.buffer, encoding=self._encoding)
                return stdin
            elif 'w' in self._mode:
                stdout = TextIOWrapper(sys.stdout.buffer, encoding=self._encoding)
                return stdout
            else:
                raise ValueError(f'argument "-" with mode {self._mode}')

        # all other arguments are used as file names
        try:
            return open(string, self._mode, self._bufsize, self._encoding,
                        self._errors)
        except OSError as error:
            raise ArgumentTypeError(f"can't open '{string}': {error}")


class InvertedIndex:
    """Inverted index class implementation"""
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
                result |= self.inverted_index[word]
            else:
                result &= self.inverted_index[word]
        return list(result)

    def dump(self, filepath: str):
        """Write inverted index to disk"""
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
        """Load inverted index from disk"""
        print(f"load inverted index from filepath {filepath}", file=sys.stderr)
        with open(filepath, "rb") as fin:
            encoding = 'utf-8'
            data = fin.read()
            (index_len,), data = struct.unpack("I", data[:4]), data[4:]
            inverted_index = defaultdict(set)

            for _ in range(index_len):
                (key_len,), data = struct.unpack("I", data[:4]), data[4:]
                key, data = data[:key_len].decode(encoding), data[key_len:]
                (vals_num,), data = struct.unpack("I", data[:4]), data[4:]
                for _ in range(vals_num):
                    (val,), data = struct.unpack("I", data[:4]), data[4:]
                    inverted_index[key].add(val)

            inverted_index = InvertedIndex(inverted_index)
            return inverted_index


def load_documents(filepath: str) -> dict:
    """Load documents to build inverted index"""
    result = {}
    with open(filepath, "r") as fin:
        for article in fin:
            article = article.strip().split(sep='\t', maxsplit=1)
            result[int(article[0])] = article[1]
    return result


# def load_stop_words(filepath: str) -> str:
    # """Load stop words from file"""
    # with open(filepath, "r") as fin:
        # return fin.read().strip()


def build_inverted_index(documents: dict) -> InvertedIndex:
    """Build inverted index for provided documents"""
    inverted_index = defaultdict(set)
    # stop_words = load_stop_words(DEFAULT_STOPWORDS_PATH)
    for i, document in documents.items():
        # document = re.sub(r"\W+", " ", document)
        # for term in document.lower().split():
        for term in document.split():
            # if (re.search(term, stop_words) is None) and (i not in inverted_index[term]):
            # if i not in inverted_index[term]:
            inverted_index[term].add(i)
    inverted_index = InvertedIndex(inverted_index)
    return inverted_index


def callback_build(arguments):
    """Callback function to build the inverted index"""
    return process_build(arguments.dataset_filepath, arguments.inverted_index_filepath)


def process_build(dataset_filepath, inverted_index_filepath):
    """The function that builds the inverted index"""
    documents = load_documents(dataset_filepath)
    inverted_index = build_inverted_index(documents)
    inverted_index.dump(inverted_index_filepath)


def callback_query(arguments):
    """Callback function to query against the inverted index"""
    return process_queries(arguments.inverted_index_filepath, arguments.query_file)


def process_queries(inverted_index_filepath, query_file):
    """The function that performs querying against the inverted index"""
    inverted_index = InvertedIndex.load(inverted_index_filepath)
    for query in query_file:
        query = query.strip()
        print(f"Use the following query to run against InvertedIndex: {query}")
        result = inverted_index.query(query.split())
        print(",".join([str(x) for x in result]))


def setup_parser(parser):
    """The function to setup parser arguments"""
    subparsers = parser.add_subparsers(help="choose command")

    build_parser = subparsers.add_parser(
        "build",
        help="build inverted index and save result in binary format on disk",
        formatter_class = ArgumentDefaultsHelpFormatter,
    )

    build_parser.add_argument(
        "-d", "--dataset",
        default=DEFAULT_DATASET_PATH,
        dest="dataset_filepath",
        help="path to dataset to load, default path is %(default)s",
    )
    build_parser.add_argument(
        "-o", "--output",
        default=DEFAULT_INVERTED_INDEX_SAVE_PATH,
        dest="inverted_index_filepath",
        help="path to store inverted index in binary format",
    )
    build_parser.set_defaults(callback=callback_build)

    query_parser = subparsers.add_parser(
        "query",
        help="query inverted index",
        formatter_class = ArgumentDefaultsHelpFormatter,
    )
    query_parser.add_argument(
        "-i", "--index",
        default=DEFAULT_INVERTED_INDEX_SAVE_PATH,
        dest="inverted_index_filepath",
        help="path to load inverted index in binary format",
    )
    query_file_group = query_parser.add_mutually_exclusive_group(required=True)
    query_file_group.add_argument(
        "--query-file-utf8",
        dest="query_file",
        type=EncodedFileType("r", encoding="utf-8"),
        default=TextIOWrapper(sys.stdin.buffer, encoding="utf-8"),
        help="query file to get queries for inverted index",
    )
    query_file_group.add_argument(
        "--query-file-cp1251",
        dest="query_file",
        type=EncodedFileType("r", encoding="cp1251"),
        default=TextIOWrapper(sys.stdin.buffer, encoding="cp1251"),
        help="query file to get queries for inverted index",
    )
    query_parser.set_defaults(callback=callback_query)


def main():
    """Main module function"""
    parser = ArgumentParser(
        prog="inverted-index",
        description="A tool to build, dump, load, and query inverted index.",
        formatter_class = ArgumentDefaultsHelpFormatter,
    )
    setup_parser(parser)
    arguments = parser.parse_args()
    arguments.callback(arguments)


if __name__ == "__main__":
    main()
