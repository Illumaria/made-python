import pytest


def get_words(text):
    return text.split()


def test_get_words_can_split_line_correctly():
    text = " one or another      word, test  "
    expected_words = ["one", "or", "another", "word,", "test"]
    words = get_words(text)
    assert expected_words == words, (
        "expected words and parsed words are not the same"
   )


def test_get_words_return_empty_list_for_empty_test():
    text = ""
    expected_words = []
    words = get_words(text)
    assert expected_words == words


def test_get_words_raise_exception_for_none():
    with pytest.raises(AttributeError):
        get_words(None)

