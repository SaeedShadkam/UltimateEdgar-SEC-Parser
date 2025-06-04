# Ultimate Edgar SEC Parser

Ultimate Edgar SEC Parser is a set of Python scripts that extract section text from SEC 10‑Q and 10‑K filings. The core logic lives in `src/Class_Function.py` which defines `Disclosure` and `Disclosure_10K` classes. Each instance downloads a filing, removes tables, finds section titles that start with “Item”, and retrieves the text for each section.

The repository currently contains example processing code in `src/Disclosure_Cleaner.py`. It loops through multiple filings, loads each one, removes tables, finds sections and returns a dictionary mapping section titles to the raw text. A helper `paragraph_splitter` function can break up long paragraphs but will be removed in future versions.

## Quick Example
```python
from src.Class_Function import Disclosure

# Observation is a pandas Series with keys: cik, TXTAddress, DisclosureAddress, CompanyName, FormType, DateFiled
filing = Disclosure.Initializer(observation)
filing.Load()
filing.Remove_Tables()
filing.Section_Finder_html()
filing.Section_text_Finder()

sections = {}
for i in range(len(filing.True_Items)-1):
    sections[filing.True_Items[i]] = filing.sections_text[i]
```
`sections` will contain entries like `"Item 1. Financial Statements."` mapped to the text for that item.

## Future Goals
The project aims to become an easy command‑line utility that accepts a document path from a user and returns a dictionary of section titles and their cleaned text. The `paragraph_splitter` helper is planned to be deprecated.

## License
This project is released under the [MIT License](LICENSE).
