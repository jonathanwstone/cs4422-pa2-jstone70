
from indexer import load_index
from indexer import load_corpus
import collections
import heapq
import math
from preprocess import tokenize
import os
import argparse


def term_score(idf_value, tf, dl, avgdl, k1,b):
    lengthFactor = 1-b+b*dl/avgdl
    tf = ((k1+1)*tf) / (k1 * lengthFactor + tf)
    return idf_value * tf

def bm25(index, query_terms, k1=1.2, b=0.75, idf_mode="plus1"):
    postings = index["postings"]
    docs = index["docs"]
    stats = index["stats"]
    N = stats["N"]
    avgdl = stats["avgdl"]

    scores = {}
    queryTerms = collections.Counter(query_terms)
    for term, q_count in queryTerms.items():
        if term not in postings:
            continue
        df = stats["df"][term]
        idf_value = idf(N, df, idf_mode)
        for doc_index, pos_list in postings[term]:
            tf = len(pos_list)
            dl = docs[doc_index]["length"]
            contribution = q_count * term_score(idf_value, tf, dl, avgdl, k1, b)
            scores[doc_index] = scores.get(doc_index, 0) + contribution
    return scores

def idf(N,df,mode):
    if mode == "raw":
        return math.log((N - df + 0.5) / (df + 0.5))
    if mode == "plus1":
        return math.log((1 + (N - df + 0.5) / (df + 0.5)))
    if mode == "floor":
        compare = math.log((N - df + 0.5) / (df + 0.5))

        return max(0.0,compare)
    raise ValueError(f"unknown idf mode: {mode}")

def sort_key(kv):
    doc_index = kv[0]
    score = kv[1]
    return score, -doc_index

def rank (scores, k=100):
    return heapq.nlargest(k, scores.items(), key=sort_key)

def search(index, query_text, k1=1.2, b = 0.75, idf_mode = "plus1", k =100):
    terms = tokenize(query_text)
    scores = bm25(index, terms, k1, b, idf_mode)
    return rank(scores,k)

def run_batch(index, topics, tag, out_path, k1=1.2, b=0.75, idf_mode="plus1", k=100):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as file:
        for item in topics:
            results = search(index, item["query"], k1, b, idf_mode, k)
            for rank_no, (doc_index, score) in enumerate(results,start=1):
                doc_id = index["docs"][doc_index]["doc_id"]
                file.write(f"{item['qid']} Q0 {doc_id} {rank_no} {score:.8f} {tag}\n")

def main():
    parser = argparse.ArgumentParser(description="Search the KSU index")
    parser.add_argument("--index-dir", default="index", help="folder containing index.pkl")
    parser.add_argument("--topics", default="data/topics.jsonl", help="topics file")
    parser.add_argument("--out-dir", default="runs", help="folder for the run file")
    parser.add_argument("--k1", type=float, default=1.2, help="BM25 k1")
    parser.add_argument("--b", type=float, default=0.75, help="BM25 b")
    parser.add_argument("--idf-mode", default="plus1", choices=["plus1", "floor", "raw"], help="IDF handling")
    parser.add_argument("--tag", default=None, help="run name (built from the settings if omitted)")
    parser.add_argument("--k", type=int, default=100, help="results per topic")
    args = parser.parse_args()

    tag = args.tag or f"bm25_k{args.k1}_b{args.b}_{args.idf_mode}"
    out_path = os.path.join(args.out_dir, tag + ".run")
    index = load_index(args.index_dir)
    topics = load_corpus(args.topics)
    run_batch(index = index, topics = topics, tag = tag, out_path= out_path,  k1 = args.k1, b = args.b, idf_mode=args.idf_mode, k = args.k)

    print(f"wrote {out_path} ({len(topics)} topics)")

if __name__ == "__main__":
    main()
