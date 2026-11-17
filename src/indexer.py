import json
import collections
import os
import pickle
import statistics

from preprocess import  normalize_line, tokenize
import argparse
import time
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

def main():
    parser = argparse.ArgumentParser(description="Build the inverted index")
    parser.add_argument("--corpus", default="data/corpus.jsonl", help="input corpus")
    parser.add_argument("--out-dir", default="index", help="folder for the index file")
    parser.add_argument("--stats-out", default="artifacts/index_stats.json")
    parser.add_argument("--gap", type=int, default=100, help="title/body position gap")
    parser.add_argument("--limit", type=int, default=None, help="index only the first N pages")
    args = parser.parse_args()
    start = time.time()
    pages = load_corpus(args.corpus)

    config = {
        "gap" : args.gap,
        "stopwords" : "nltk english",
        "boilerplate_threshold" : None,
        "tokenizer" : "lowercase, whitespace split, edge punctuation stripped, letter-hyphen-letter split, NLTK stopwords removed"
    }

    if args.limit:
        pages = pages[:args.limit]

    idx = build_index(pages, config)
    path = save_index(idx, args.out_dir)
    build_seconds = time.time()-start
    lengths = [d["length"] for d in idx["docs"]]
    report = {
        "num_docs" : idx["stats"]["N"],
        "total_tokens": idx["stats"]["total_tokens"],
        "avgdl": idx["stats"]["avgdl"],
        "num_terms": len(idx["postings"]),
        "num_postings": sum(idx["stats"]["df"].values()),
        "index_bytes_on_disk": os.path.getsize(path),
        "build_seconds": build_seconds,
        "preprocessing": config,
        "median_doc_length": statistics.median(lengths),
        "min_doc_length" : min(lengths),
        "max_doc_length" : max(lengths),
        "mean_doc_length": statistics.mean(lengths),
        "zero_length_docs": sum(1 for n in lengths if n == 0)

    }
    print(report)

    os.makedirs(os.path.dirname(args.stats_out), exist_ok= True)
    with open(args.stats_out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    main()