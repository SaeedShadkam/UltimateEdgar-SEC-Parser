# Ultimate EDGAR SEC Parser

Extract narrative sections (Items) from 10-Q and 10-K filings on the SEC EDGAR site, at scale. This repo provides a small pipeline to index filings, optionally download raw submissions, and parse core disclosures into clean, paragraph-sized chunks you can use for downstream NLP.

## Purpose and goals

- Build a reproducible workflow to turn raw EDGAR filings into structured, analysis-ready text.
- Focus on narrative sections (e.g., MD&A, Risk Factors, Controls and Procedures) rather than numerical tables.
- Handle real-world HTML variability using pragmatic heuristics and fuzzy matching.
- Keep the code simple enough to read and extend (resume and portfolio friendly).

## What’s included

- `src/edgar_classes.py` — Core parsing engine for 10-Q and 10-K filings
	- Loads each filing’s TXT (HTML source), normalizes it, removes table-y content, finds Item headers, and extracts the per-Item text.
	- Heuristics use regex + Levenshtein fuzzy matching against official SEC item titles.

- `src/Disclosure_Cleaner.py` — Orchestrates parsing
	- Reads `src/ListofDisclosurestoParse.csv` (CIK, Year, Quarter) and merges with the EDGAR index to get URLs.
	- Runs the parser and writes one pickle per target filing to `src/output/CIK_Year_Quarter.pkl`.

- `src/Financial Statement Dataset/edgar_sub_database.csv` — EDGAR submissions index
	- A union of quarterly sub.txt files with helpful columns like `cik, fy, fp, form, filed, name, html_url, txt_url`.
	- If you don’t have this yet, see “Build the index” below.


## How to use

### 1) Install dependencies

Python 3.9+ recommended.

Required packages:

- pandas
- requests
- beautifulsoup4
- html5lib
- python-Levenshtein
- numpy

PowerShell (Windows) example:

```pwsh
pip install pandas requests beautifulsoup4 html5lib python-Levenshtein numpy
```

SEC usage note: Provide a meaningful User-Agent that includes contact info if you’re doing large crawls. In this repo, `Disclosure_Cleaner.py` uses a placeholder `user_api` you can customize.

### 2) Build the index (if you don’t have it yet)

If `src/Financial Statement Dataset/edgar_sub_database.csv` is missing, generate it from your quarterly `sub.txt` files.

```pwsh
python src/read_sub_txt.py
```

This scans `src/Financial Statement Dataset/<year>q<quarter>/sub.txt` folders, concatenates them, and writes `edgar_sub_database.csv` with `html_url` and `txt_url` columns.

### 3) Prepare your target list

Create `src/ListofDisclosurestoParse.csv` with columns:

```
CIK,Year,Quarter
320193,2023,Q3
789019,2022,FY
```

### 4) Run the parser

```pwsh
python src/Disclosure_Cleaner.py
```

Outputs will be written to `src/output/CIK_Year_Quarter.pkl`. Each pickle is a dict that maps item titles (e.g., “Item 2. Management’s Discussion…”) to a list of paragraph-sized chunks.


## Heuristics overview

The parsing engine (`Disclosure` for 10‑Q, `Disclosure_10K` for 10‑K) follows this sequence:

1) Load + parse
	 - Fetches the filing’s TXT (HTML source) with `requests` using your User-Agent.
	 - Parses HTML with BeautifulSoup (`html.parser`), falling back to `html5lib` for messy cases.

2) Remove tables and reduce noise
	 - Remove hyperlink-based TOC tables (anchors like “table of contents” or `href="#..."`).
	 - Remove colored tables via CSS `background-color` or HTML `bgcolor` attributes.
	 - Remove “mostly numeric” tables by pattern matching (currency/number-like cells).
	 - These passes leave narrative sections (MD&A, Risk Factors, etc.) more prominent.

3) Find Item headers
	 - Regex to find text starting like `Item …` (case-insensitive), then build a neighborhood string around each candidate.
	 - Clean and normalize that neighborhood text.
	 - Fuzzy-match against official SEC item titles using Levenshtein distance (normalized by word count).
	 - Apply a keyword gate (“Final_Item_Checker”) to filter false positives.
	 - Deduplicate repeated headers (e.g., “continued”) so one Item doesn’t get split into multiple sections.
	 	 - Example headers found in a single filing:
	 	 	 - “Item 2. Management’s Discussion and Analysis of Financial Condition and Results of Operations.”
	 	 	 - “Item 2. Management’s Discussion and Analysis of Financial Condition and Results of Operations. (continued)”
	 	 - Result: we keep one canonical header for Item 2 and merge the text under that single Item key in the output.

4) Extract section text
	 - Locate each header in the raw HTML text and slice out the content span for each Item.
	 - Output: a dict from Item title → section text; `Disclosure_Cleaner.py` then splits into paragraph chunks.

5) Chunk into paragraphs
	 - `paragraph_splitter` assembles sentences until a word budget is reached (default ~400 words).
	 - If a single sentence exceeds budget, it falls back to a whitespace split.

Diagnostics:
- The code keeps global buckets like `Old_HTMLs`, `Not_Well_Parsed`, and `String_Not_Available` for triage. These are helpful for QA runs but are not thread‑safe.

## Output format

Per filing, a pickle at `src/output/CIK_Year_Quarter.pkl`:

```python
{
	"Item 2. Management’s Discussion and Analysis of Financial Condition and Results of Operations.": [
		"Paragraph chunk 1 (<= ~400 words)",
		"Paragraph chunk 2",
		...
	],
	"Item 1A. Risk Factors.": [
		...
	],
	...
}
```

## Design notes and limitations

- Pragmatic over perfect: heuristics are tuned for “typical” EDGAR pages; unusual markup can still trip it up.
- No automatic retries/backoff on network calls — if you need higher robustness, add a tiny retry wrapper.
- Diagnostics use module-level globals; keep runs single-threaded or refactor to structured results for concurrency.
- The official title lists cover common forms of 10‑Q/10‑K Items; if your corpus is niche, extend the lists.

## Project structure

```
src/
	edgar_classes.py                # Core parsing classes + utilities
	Disclosure_Cleaner.py           # Orchestrates parsing and writes per‑filing pickles
	read_sub_txt.py                 # Builds the unified index CSV from quarterly sub.txt files
	Financial Statement Dataset/    # Quarterly folders and edgar_sub_database.csv
```

## License

This project is licensed under the terms of the LICENSE in this repository.

## Contact / User‑Agent

EDGAR requests should include a contact in the User‑Agent (per SEC guidance). In this repo, the default is a placeholder. Please replace it with your own contact details when crawling at scale.

