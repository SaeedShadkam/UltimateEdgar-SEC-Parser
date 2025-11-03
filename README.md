# UltimateEdgar-SEC-Parser

A small Python toolkit to download and parse SEC EDGAR disclosure filings (10-Q / 10-K style forms). The project focuses on cleaning HTML/text filings, removing numeric/tables and table-of-contents noise, locating standard SEC "Item" sections (e.g. Item 1, Item 7) and extracting each section's text for downstream NLP or data processing.

This repository contains parsing utilities built around BeautifulSoup plus heuristics (Levenshtein matching and keyword checks) to robustly identify official SEC items despite variation in formatting.

## Highlights
- Download and parse SEC filing text (from SEC Archives) using a stable user-agent header.
- Remove numeric and colored tables (to avoid extracting tabular financial data as narrative).
- Locate and normalize standard SEC items (10-K and 10-Q style) and split each filing into per-item text blocks.
- Provide a paragraph splitting helper to break long sections into smaller pieces.

## Files
- `src/Class_Function.py` — Core parsing module. Exposes:
	- `Disclosure` and `Disclosure_10K` classes: load a filing, remove tables, find Item headings and extract section text.
	- `Official_Items`, `Official_Items_10K`, and associated keyword lists used to match item headings.
	- `paragraph_splitter(doc, max_words_document)` helper.
- `src/classes2.py` — Driver script that shows how to iterate through a CSV of matched filings, initialize `Disclosure` / `Disclosure_10K`, process filings, split paragraphs, and save results. Contains an example batch processing loop.
- `src/Disclosure_Cleaner.py` — (If present) additional orchestration logic and helper functions used by the processing pipeline.

## Dependencies
This project expects the following Python packages (typical install):

- Python 3.8+
- requests
- beautifulsoup4
- python-Levenshtein
- pandas
- numpy
- html5lib

Install with pip:

```powershell
pip install requests beautifulsoup4 python-Levenshtein pandas numpy html5lib
```


## Quick usage
Minimal interactive example (from project root):

1. Import the classes (example):

```python
from src.Class_Function import Disclosure, Disclosure_10K

# Example values (replace with real values from SEC index):
cik = '0000123456'
txt_path = 'edgar/data/0000123456/0000123456-00-000000.txt'  # path suffix from SEC archives
html_path = 'edgar/data/0000123456/0000123456-00-000000.htm'
company = 'Example Corp'
form_type = '10-Q'
date_filed = '2020-01-01'

disclosure = Disclosure(cik, txt_path, html_path, company, form_type, date_filed)
disclosure.Load()
disclosure.Remove_Tables()
disclosure.Section_Finder_html()
disclosure.Section_text_Finder()

# extracted sections:
for title, text in zip(disclosure.True_Items, disclosure.sections_text):
		print('===', title)
		print(text[:800])
```

Important: set a meaningful User-Agent header when requesting SEC archives (the SEC requires identifying headers). The classes already accept a default, but replace it with your contact info for large crawls.

## Notes & caveats
- The parser uses heuristics (Levenshtein distance + keyword checks) to match item headings. It works well on many filings but will fail on heavily malformed or very old HTML. The code tracks `Old_HTMLs`, `Not_Well_Parsed`, and `String_Not_Available` to flag problematic files.
- The code removes tables aggressively to avoid extracting numeric tables as narrative text. If you need the tables (financials), consider adjusting or disabling the table-removal methods.
- There are many SEC formatting edge cases — treat this as a pragmatic extractor, not a perfect canonical parser.

## Suggested next steps (small, low-risk improvements)
1. Add a small unit test suite verifying: loading a simple saved HTML sample, table removal works, and Section_Finder_html finds expected items.
2. Move magic constants (official item lists) to a small JSON resource file so they are easier to maintain.
3. Add type hints and a short usage script (CLI) for processing one URL or TXT path.

## License
See the repository LICENSE file.

----

If you want, I can:
- Add a short example script under `examples/` and an automated test harness (pytest) with one or two sample HTML files.
- Tidy up docstrings and add type annotations across `src/Class_Function.py`.

Tell me which follow-up you'd like and I will implement it next.

