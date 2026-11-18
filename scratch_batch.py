import sys
from collections import Counter
sys.path.insert(0, "src")
from indexer import load_index, load_corpus
from search import run_batch

idx = load_index("index")
topics = load_corpus("data/topics.jsonl")[:3]
run_batch(idx, topics, "test_run", "tmp/test.run")

with open("tmp/test.run", encoding="utf-8") as f:
    lines = f.read().splitlines()

print(len(lines), "lines")
print(Counter(line.split()[0] for line in lines))
for line in lines[:5]:
    print(line)