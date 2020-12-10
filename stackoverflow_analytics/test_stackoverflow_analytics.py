from stackoverflow_analytics import (
    load_stop_words,
)

DEFAULT_STOP_WORDS_FPATH = "stop_words_in_koi8r.txt"
DEFAULT_QUESTIONS_FPATH = "questions_sample.xml"


def test_can_open_xml_file():
    with open(DEFAULT_QUESTIONS_FPATH, "r") as questions_fin:
        content = questions_fin.read()
        assert "SQL Server 2008" in content


def test_load_stop_words_returns_correct_value_type():
    with open(DEFAULT_STOP_WORDS_FPATH, "r", encoding="koi8-r") as fin:
        stop_words = load_stop_words(fin)
        assert isinstance(stop_words, set)
