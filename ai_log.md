# AI Usage Log (docs/ai_log.md)

**Group:** solo
**Member:** Jon Stone (<netid: jstone70>, <GitHub username: jonathanwstone>)
**Assistant:** Claude (chat interface). Used as a tutor: concepts, planning, code review, and debugging help. All project code in `src/` was written by me; short snippets the assistant supplied are listed explicitly under "Snippets supplied by the assistant" below.

> Dates below are the days of the sessions. Edit any entry that does not match what you actually did.

---

## Session 1: Sun Nov 15 (planning, preprocessing decisions, index design)

**What I asked**
- Help understanding the PA2 instructions and how to plan the work.
- Estimated hours and a day-by-day schedule through the Nov 29 deadline (the instructor confirmed the 29th by email/in person).
- What to reuse from PA1 (I uploaded `analyze.py` and `crawler.py`).
- How to decide preprocessing and how to structure the indexer.

**What the assistant told me / what I learned**
- The AI policy (§0) means tutor, not co-author, so I write the code and log how I used help.
- Estimated 56-74 hours total; at my PA1 pace (1-2 hrs/day) that does not fit, so I committed to 3-4 hrs/day.
- From PA1 reuse: the stopword list (NLTK), the line-frequency boilerplate idea, `loadJson`, and argparse structure are reusable. `TfidfVectorizer` in PA1's `analyze.py` is banned in PA2 (Req 3), so it must not appear anywhere in this repo. Crawler code is not relevant. Estimated net saving was only 2-3 hours.
- Preprocessing choices have consequences: splitting only on whitespace leaves punctuation attached (`aid.` vs `aid`); hyphen splitting changes matching; any boilerplate threshold is a development decision and must be justified on the train topics only (Req 10).
- Index design concepts: positional postings, why tf can be `len(positions)`, why a title/body position gap stops phrases from matching across the boundary, and why document length must be the token count rather than the last position (otherwise the gap inflates every length and distorts BM25 and query likelihood).

**Decisions I made**
- Lowercase everything; NLTK stopwords (as in PA1); whitespace split with leading/trailing punctuation stripped; hyphens between two letters are split (`financial-aid` -> `financial`, `aid`), hyphens touching a digit are kept (`578-6000`).
- Index the title together with the text, no field weight for now.
- Store positions only (tf = `len(positions)`); stopwords are not stored, so positions are numbered after stopword removal; title and body are separated by a gap (100) so phrases cannot span them.
- Store the document text inside the index so search never reads the corpus.

**Hand exercise (3 made-up documents A, B, C)**
- I built token lists and positions by hand. Mistakes I made and corrected: I numbered a one-token title as position 1 (positions start at 0); I gave document C a "length" of 104 (last position + 1, gap-inflated) when the true length is 4 tokens.
- My totals matched: 18 total tokens, avgdl 6.0.
- 
**Assistant errors I noticed**
- It first labelled Nov 14 as "Saturday" and built the schedule from the wrong date; it re-based the schedule on Nov 15 once corrected.

---

## Session 2: Mon Nov 16 (building and testing the indexer)

For each function: I wrote it, pasted it, the assistant pointed out bugs without rewriting it, and I fixed them and re-tested.

**`load_corpus`**
- Bugs I had: `json.load` on the whole file instead of `json.loads` per line; hardcoded Windows path that ignored the `path` argument; the `ValueError` was created but never raised, so malformed lines would be skipped silently.
- Verified: `len(pages) == 1965`, first record has keys `doc_id, url, title, text, out_links`.

**Boilerplate (`normalize_line`, `find_boilerplate`)**
- Adapted from PA1. Bugs I had: `line.split` without parentheses; threshold argument ignored (hardcoded half of pages); no handling of `None`.
- I wrote a scratch script that counted on how many pages each line appears. Result: **0 lines flagged at thresholds 0.5, 0.3 and 0.1**, with every line count equal to 1. Cause found by checking: **0 of 1,965 pages contain more than one line**; each page's text is a single long line, so the PA1 line-frequency method cannot work on this corpus.
- Decision: the baseline index is built unstripped (threshold `None`). A phrase-level boilerplate filter (repeated runs of words, not lines) is a candidate Q5.b fix, to be developed on train topics only. The repeated headers I saw ("Skip to main content", repeated menu text, the "Fall Special - Save $450" banner) are the predicted failure evidence.

**`tokenize`**
- Bugs I had: a stray trailing backslash; editing the loop variable (`token = ""`) instead of building a new list; an `== "-"` check that never fires because stripping already turns a lone hyphen into an empty string; stopword set must be loaded once at module level, not per call.
- Verified on five test strings, all matching expected output, including the banner line `‹ Back to Kennesaw State Fall Special - Save $450. Enroll Today!` with no empty tokens.

**`index_document`**
- Bugs I had: `positions` keyed by position instead of by term (inverted); hardcoded 100 instead of `len(title_tokens) + gap`; length via `len(positions)` (counts distinct terms); `=` overwriting instead of appending to a list.
- Verified on the three hand pages: A `financial` = `[0, 103]`, B `registrar` = `[0, 101]`, C `parking` = `[100]`, lengths 7, 7, 4.

**`build_index`**
- Bugs I had: postings overwritten with `=` instead of appended; `docs.append` used a set instead of a dict and called `index_document` a second time; `totalTokens` never updated; `growth` pair recorded document length instead of vocabulary size (would have corrupted the Heaps' law fit); `df`/`cf` loop used a list as a dict key and `len([postings[term]])` (always 1); malformed return dictionary keys.
- Understood: `df` = number of documents containing the term, `cf` = total occurrences; checks `sum(lengths) == total_tokens` and `sum(cf) == total_tokens`.
- 
**`save_index` / `load_index`**
- Bugs I had: `with open` outside the function; `os.path.join` result unused; `encoding=` passed in binary mode; `return path.main()`; unnecessary `makedirs` in the loader.
- 
---

## Snippets supplied by the assistant (not written by me)

- `normalize_line`: `" ".join(line.split())`
- The hyphen rule regex: `re.sub(r"(?<=[a-z])-(?=[a-z])", " ", text)`
- The edge-character constant idea (`string.punctuation` plus `‹ › •`) and module-level stopword set
- The `dict.setdefault(...).append(...)` pattern (I used an explicit `if term not in` form)
- The shape of the doc-table dict and the `stats` dict keys
- Scratch test scripts for `load_corpus`, boilerplate counting, `tokenize`, `index_document`, and `build_index`

## How I verified results (not just trusting the assistant)

- Hand-built the 3-document example before coding and compared code output to it.
- Counted pages (1,965) and checked record keys after loading.
- Measured the boilerplate filter on the real corpus and inspected the output instead of assuming PA1's method would transfer.
- Ran `tokenize` on real banner text and asserted no empty tokens.
- Correctness checks to run on the full build: `sum(doc lengths) == total_tokens`, `sum(cf) == total_tokens`, save/load round trip equality.

## Still to do

- `main()` with argparse, `artifacts/index_stats.json`, full 1,965-page build
- BM25, evaluation, TF-IDF, query likelihood, tuning on train only, Q1-Q5

---

## Session 3: Tue Nov 17 (main(), index_stats.json, full corpus build)

As before: I wrote each piece, pasted it, the assistant pointed out bugs without rewriting my code, and I fixed and re-tested.

**What I asked**
- How to structure `main()` with argparse for the indexer stage, what goes into the saved config, and what goes into `artifacts/index_stats.json`.
- How to run the script from the PyCharm terminal, and how to fix path errors.
- The difference between the stats dict stored inside the index and the report dict written to JSON.

**Bugs I had and fixed**
- `config` was used in `build_index(pages, config)` before it was defined (NameError).
- `save_index` was called twice in a row.
- `os.makedirs(...)` line was missing a closing parenthesis (syntax error), and I assigned its result to a variable; `makedirs` returns `None`, so the following `open` would have failed.
- `num_postings` was `sum(idx["stats"]["avgdl"])`, which sums a single float and raises a TypeError; the correct value is the sum of the `df` values (number of term-document pairs).
- `min_doc_length` and `max_doc_length` used `median_low` / `median_high` (variants of the median) instead of `min` / `max`.
- Report key was `"N"` but the assignment names it `num_docs`.
- I first confused the two "stats" dicts: `idx["stats"]` (built by `build_index`, used for scoring: N, total_tokens, avgdl, df, cf, growth) versus the `report` dict (built in `main()`, written to `index_stats.json`, human-readable summary).

**Environment problems and how I found them**
- `python src/indexer.py` failed because `indexer.py` was in the project root, not `src/`. I moved `indexer.py` and `preprocess.py` into `src/` to match the required layout (§3.2).
- `FileNotFoundError: data/corpus.jsonl`: the corpus was at `artifacts/data/`, not `data/` at the repo root. I located it with `Get-ChildItem -Recurse -Filter corpus.jsonl` and moved the folder to `data/`. I checked that `data/` and `index/` are in `.gitignore` and not tracked (the assignment says not to commit them).

**Results**
- 20-page test run matched my earlier hand-built check: 20 docs, 21,462 tokens, avgdl 1073.1, 2,422 terms, 10,139 postings, 0 zero-length docs.
- Verified the `enroll` postings against the printed output: 16 documents (df) and position-list lengths summing to 106 (cf).
- Full build (`python src/indexer.py`): 1,965 docs, 1,333,777 tokens, avgdl 678.77, 37,177 terms, 643,611 postings, 24.2 MB on disk, 2.6 s build time, 0 zero-length docs. Document length: min 45, median 550, mean 679, max 12,844.
- Correctness checks on the full saved index (loaded from disk): `len(docs) == N`, `sum(doc lengths) == total_tokens`, and `sum(cf) == total_tokens`, all true.
- Longest page is `ksu-1957` (https://www.kennesaw.edu/visit/campus-tours/, 12,844 tokens, about 19x the average). Noted as a candidate for Q2 (length normalization) and Q5. [Edit: after I looked at what fills this page, what I found.]

**Observations to use in the analysis**
- On the first 20 pages, `enroll` appears at identical positions (118, 131, 139, 140) in several different cpe course pages (doc indexes 1, 7, 10, 11), including adjacent positions 139 and 140. This is the shared page template, which is direct evidence of boilerplate matching (candidate Q5 diagnosis).
- Vocabulary is inflated by my tokenizer choices (phone numbers, emails, and dollar amounts each become terms); this matters for the Heaps' law fit in Q1.b.
- The stored index includes the page text, so `index_bytes_on_disk` is larger than a postings-only index.

**Decisions**
- Saved config in the index: gap 100, NLTK English stopwords, boilerplate threshold `None` (baseline is unstripped), and a tokenizer description. `index_stats.json` includes the config as `preprocessing`, plus mean/median/min/max document length and zero-length count for Q2.
- `growth` (tokens seen, vocabulary size) stays inside the index and will be used for the Heaps' law fit; it is not written to `index_stats.json`.

**Snippets supplied by the assistant (not written by me)**
- The argparse argument list and the general order of steps in `main()`.
- The keys for `config` and the mapping from `idx["stats"]` to the report fields.
- The verification script (`sum(lengths) == total_tokens`, `sum(cf) == total_tokens`, longest page lookup).
- PowerShell commands for locating and moving files.

**How I verified**
- Compared the 20-page output to my earlier hand checks and the `enroll` df/cf to the printed postings.
- Ran the three consistency checks on the full index after loading it from disk.
- Checked `git status` that `data/` and `index/` are not committed.

**Next**
- BM25 in `src/search.py`. Open decision: how to handle the IDF going negative for terms in more than half the documents (floor at zero vs. adding 1 inside the log). Plan is to check the highest-df terms in the corpus first and justify the choice on train topics.