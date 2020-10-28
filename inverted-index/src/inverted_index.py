from collections import defaultdict


import pickle


class InvertedIndex:
    def __init__(self, documents: dict):
        self.inverted_index = defaultdict(list)
        for i, document in documents.items():
            for term in document.split():
                term = term.strip(",.!?")
                if i not in self.inverted_index[term]:
                    self.inverted_index[term].append(i)


    def query(self, words: list) -> list:
        """Return the list of relevant documents for the given query"""
        result = set()
        for word in words:
            if len(result) == 0:
                result.update(self.inverted_index[word])
            else:
                result = result & set(self.inverted_index[word])
        return list(result)

    def dump(self, filepath: str):
        with open(filepath, "wb") as fout:
            pickle.dump(self.inverted_index, fout)

    @classmethod
    def load(cls, filepath: str):
        with open(filepath, "rb") as fin:
            inverted_index = pickle.load(fin)
            return inverted_index


def load_documents(filepath: str) -> dict:
    result = {}
    with open(filepath, "r") as fin:
        for line in fin:
            line = line.strip().split(sep='\t')
            result[line[0]] = line[1]
    return result


def build_inverted_index(documents: dict) -> InvertedIndex:
    result =  InvertedIndex(documents)
    return result


def main():
    documents = load_documents("../resources/wikipedia_sample")
    inverted_index = build_inverted_index(documents)
    inverted_index.dump("/path/to/inverted.index")
    inverted_index = InvertedIndex.load("/path/to/inverted.index")
    document_ids = inverted_index.query(["two", "words"])


if __name__ == "__main__":
    main()
