#!/usr/bin/env python3
from argparse import ArgumentDefaultsHelpFormatter
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from argparse import FileType
from collections import defaultdict
from io import TextIOWrapper
# import re
import sys

DEFAULT_QUESTIONS_FPATH = "questions.xml"
DEFAULT_STOP_WORDS_FPATH = "stop_words_in_koi8r.txt"


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


def process_arguments(questions_filepath, stopwords_filepath, query_file):
    pass


def callback_parser(arguments):
    """Callback function"""
    return process_arguments(arguments.questions_filepath,
                             arguments.stopwords_filepath,
                             arguments.query_file)


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
        type=EncodedFileType("r", encoding="koi8r"),
        # default=TextIOWrapper(sys.stdin.buffer, encoding="koi8r"),
        help="path to stop-words file in text format",
    )
    parser.add_argument(
        "--queries",
        dest="query_file",
        help="query file in csv format to get queries for analytics",
    )
    parser.set_defaults(callback=callback_parser)


def main():
    """Main module function"""
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
