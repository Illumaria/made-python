from collections import defaultdict


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
                result.update(self.inverted_index[word])
            else:
                result = result & set(self.inverted_index[word])
        return list(result)

    def dump(self, filepath: str):
        with open(filepath, "wb") as fout:
            fout.write(struct.pack("I", len(self.inverted_index)))
            for key, vals in self.inverted_index.items():
                key = bytes(key, 'utf-8')
                fout.write(struct.pack(f"I{len(key)}s", len(key), key))
                fout.write(struct.pack("I", len(vals)))
                for val in vals:
                    val = bytes(val, 'utf-8')
                    # fout.write(struct.pack(f"I", val))
                    fout.write(struct.pack(f"I{len(val)}s", len(val), val))

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
                    (val_len,), data = struct.unpack("I", data[:4]), data[4:]
                    val, data = data[:val_len].decode(encoding), data[val_len:]
                    inverted_index[key].append(val)

            inverted_index = InvertedIndex(inverted_index)
            return inverted_index


def load_documents(filepath: str) -> dict:
    result = {}
    with open(filepath, "r") as fin:
        for line in fin:
            line = line.strip().split(sep='\t')
            result[line[0]] = line[1]
    return result


def build_inverted_index(documents: dict) -> InvertedIndex:
    inverted_index = defaultdict(list)
    for i, document in documents.items():
        for term in document.split():
            term = term.strip(",.!?")
            if i not in inverted_index[term]:
                inverted_index[term].append(i)
    inverted_index = InvertedIndex(inverted_index)
    return inverted_index


def main():
    documents = load_documents("../resources/wikipedia_sample")
    inverted_index = build_inverted_index(documents)
    inverted_index.dump("/path/to/inverted.index")
    inverted_index = InvertedIndex.load("/path/to/inverted.index")
    document_ids = inverted_index.query(["two", "words"])


if __name__ == "__main__":
    main()
