import sys
from collections import Counter
sys.path.insert(0, "src")
from indexer import load_corpus

run = "runs/bm25_k1.2_b0.75_plus1.run"
counts = Counter(line.split()[0] for line in open(run, encoding="utf-8") if line.strip())

topics = load_corpus("data/topics.jsonl")
train_ids = {l.split()[0] for l in open("data/qrels.train.txt") if l.strip()}

print(len(counts), "topics have results;", len(topics) - len(counts), "have none")
for t in topics:
    n = counts.get(t["qid"], 0)
    if n < 100:
        label = t["query"] if t["qid"] in train_ids else "(test topic)"
        print(f"{t['qid']}  {n:3d} results  {label}")