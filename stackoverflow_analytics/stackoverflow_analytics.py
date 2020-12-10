#!/usr/bin/env python3
from argparse import ArgumentDefaultsHelpFormatter
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from argparse import FileType
from collections import defaultdict
from io import TextIOWrapper
import logging
from lxml import etree
import re
import sys

APPLICATION_NAME = "stackoverflow_analytics"
DEFAULT_APP_HANDLER_FPATH = "stackoverflow_analytics.log"
DEFAULT_WARN_HANDLER_FPATH = "stackoverflow_analytics.warn"
DEFAULT_QUERIES_FPATH = "queries_sample.csv"
DEFAULT_SMALL_QUESTIONS_FPATH = "questions_sample.xml"
DEFAULT_BIG_QUESTIONS_FPATH = "stackoverflow_posts_sample.xml"
DEFAULT_STOP_WORDS_FPATH = "stop_words_in_koi8r.txt"



logger = logging.getLogger(APPLICATION_NAME)


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
                raise ValueError(f'Argument "-" with mode {self._mode}.')

        # all other arguments are used as file names
        try:
            return open(string, self._mode, self._bufsize, self._encoding,
                        self._errors)
        except OSError as error:
            raise ArgumentTypeError(f"Can't open '{string}': {error}.")


def load_questions(questions_filepath):
    with open(DEFAULT_BIG_QUESTIONS_FPATH, "r") as fin:
        content = fin.readlines()
        print(len(content))
        for line in content:
            root = etree.fromstring(line, parser=etree.XMLParser())
            if int(root.get("PostTypeId")) == 1:
                score = int(root.get("Score"))
                year = int(root.get("CreationDate").split('-')[0])
                title = root.get("Title")
                title_tokens = re.findall("\w+", title.lower())
                print(year, score, title_tokens)


def load_stop_words(fin) -> set:
    """Load stop words from file"""
    # with open(filepath, "r") as fin:
        # return fin.read().splitlines()
    return set(fin.read().splitlines())


def process_arguments(questions_filepath, stopwords_file, query_filepath):
    questions = load_questions(questions_filepath)
    stop_words = load_stop_words(stopwords_file)


def callback_parser(arguments):
    """Callback function"""
    return process_arguments(arguments.questions_filepath,
                             arguments.stopwords_file,
                             arguments.query_filepath)


def setup_parser(parser):
    """The function to setup parser arguments"""
    parser.add_argument(
        "--questions",
        default=DEFAULT_SMALL_QUESTIONS_FPATH,
        dest="questions_filepath",
        help="path to questions in xml format",
    )
    parser.add_argument(
        "--stop-words",
        default=DEFAULT_STOP_WORDS_FPATH,
        dest="stopwords_file",
        type=EncodedFileType("r", encoding="koi8-r"),
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
