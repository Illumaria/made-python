from collections import defaultdict
import re
import struct


class InvertedIndex:
    def __init__(self, documents: dict):
        self.inverted_index = documents

    def __eq__(self, other):
        return self.inverted_index == other.inverted_index

    def query(self, words: list) -> list:
        """Return the list of relevant documents for the given query"""
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
    result = {}
    with open(filepath, "r") as fin:
        for line in fin:
            line = line.strip().split(sep='\t')
            result[int(line[0])] = line[1]
    return result


def load_stop_words(filepath: str) -> str:
    with open(filepath, "r") as fin:
        return fin.read().strip()


def build_inverted_index(documents: dict) -> InvertedIndex:
    inverted_index = defaultdict(list)
    stop_words = load_stop_words("../resources/stop_words_en.txt")
    for i, document in documents.items():
        document = re.sub(r"\W+", " ", document)
        for term in document.lower().split():
            if (re.search(term, stop_words) is None) and (i not in inverted_index[term]):
                inverted_index[term].append(i)
    inverted_index = InvertedIndex(inverted_index)
    return inverted_index


def main():
    documents = load_documents("../resources/tiny_wikipedia_sample")
    # stop_words = load_stop_words("../resources/stop_words_en.txt")
    inverted_index = build_inverted_index(documents)
    path = "../resources/tiny_dump_3"
    # inverted_index.dump(path)
    inverted_index = InvertedIndex.load(path)
    print(inverted_index.inverted_index)
    # document_ids = inverted_index.query(["two", "words"])


if __name__ == "__main__":
    main()
