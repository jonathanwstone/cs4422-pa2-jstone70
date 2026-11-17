import json
import collections
import os
import pickle
from preprocess import  normalize_line, tokenize

indexFile = "index.pkl"
def load_corpus(path): # -> list of page dicts
    count = 0
    recordedLines = []
    with open(path, 'r', encoding = 'utf-8') as file:
        for line in file:
            count += 1
            if not line.strip():
                continue
            else:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    raise ValueError(f"Bad Json on line {count}")

                recordedLines.append(record)
    return recordedLines

def find_boilerplate(pages, threshold):  # -> set of normalized lines to drop
    repeatedLines = collections.Counter([])
    repeatSet = set()

    if threshold is None or threshold == 0:
        return repeatSet

    cutoff = threshold * len(pages)

    for entry in pages:

        for line in {n for n in (normalize_line(l) for l in entry['text'].splitlines()) if n}:
            if line:
                repeatedLines[line] += 1

    for line, count in repeatedLines.items():
        if count > cutoff:
            repeatSet.add(line)
    return repeatSet

def index_document(page, config): # -> (positions_by_term: dict[str, list[int]], length: int)
    title = page.get("title") or ""
    text = page.get("text") or ""

    titleTokens = tokenize(title)
    bodyTokens = tokenize(text)
    bodyStart = len(titleTokens) + config['gap']
    length = len(titleTokens) + len(bodyTokens)
    positions = {}

    for i, term in enumerate(titleTokens):
        if term not in positions:
            positions[term] = []

        positions[term].append(i)

    for j, term in enumerate(bodyTokens):
        if term not in positions:
            positions[term] = []

        positions[term].append(bodyStart+j)

    return positions, length

def build_index(pages, config):          # -> the index dict
    postings = {}
    docs = []
    growth = []
    totalTokens=0

    for docIndex, page in enumerate(pages):
        positions, length = index_document(page,config)

        for term, posList in positions.items():
            if term not in postings:
                postings[term]=[]
            postings[term].append([docIndex, posList])
        docs.append({
            "doc_index": docIndex,
            "doc_id": page["doc_id"],
            "url": page["url"],
            "title": page.get("title") or "",
            "text": page["text"],
            "length": length,
        })

        totalTokens = length + totalTokens
        growth.append([totalTokens, len(postings)])
    N = len(pages)
    averageDl = totalTokens / N
    df = {}
    cf = {}
    for term in postings:
        df[term] = len(postings[term])
        cf[term] = 0
        for docIndex, posList in postings[term]:
            cf[term] += len(posList)  # add this document's occurrence count

    stats = {
        "N" : N,
        "total_tokens": totalTokens,
        "avgdl" : averageDl,
        "df" : df,
        "cf": cf,
        "growth" : growth
    }

    return {"postings" : postings,
            "docs" : docs,
            "stats" : stats,
            "config" : config}

def save_index(index, out_dir):
    os.makedirs(out_dir, exist_ok= True)
    path = os.path.join(out_dir, indexFile)
    with open(path, "wb") as file:
        pickle.dump(index,file)

    return path

def load_index(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, indexFile)
    with open(path, "rb") as file:
        return pickle.load(file)

def main(): ...

if __name__ == "__main__":
    pages = load_corpus("C:/Users/jonat/PycharmProjects/CorpusSearchEngine/artifacts/data/corpus.jsonl")

    config = {"gap": 100}
    A = {"title": "Financial Aid", "text": "Apply for financial aid at the office of the registrar."}
    B = {"title": "Registrar", "text": "The registrar office handles registration and aid forms."}
    C = {"title": "", "text": "Parking permits are sold at the office."}

    for page in (A, B, C):
        positions, length = index_document(page, config)
        print(length, positions)