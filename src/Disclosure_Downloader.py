"""
Disclosure_Downloader.py (ultra-simple)

Assumes a user CSV with columns: cik, year, quarter (Q1/Q2/Q3/FY)
Per row, does a direct .loc on edgar_sub_database.csv to find matches
and downloads both txt_url and html_url (saved as .txt) without parsing.

Usage:
  python src/Disclosure_Downloader.py user_requests.csv
"""

import os
import sys
import pandas as pd
import requests


INDEX_PATH = os.path.join("src", "Financial Statement Dataset", "edgar_sub_database.csv")
OUT_DIR = "downloads"
UA = "UltimateEdgar-SEC-Parser Downloader"


def _download(url: str, dest: str) -> None:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    r = requests.get(url, headers={"User-Agent": UA}, timeout=45)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)


def main():
    if len(sys.argv) < 2:
        print("Usage: python src/Disclosure_Downloader.py <user_requests.csv>")
        return

    user_csv = sys.argv[1]
    user_df = pd.read_csv(user_csv)
    idx_df = pd.read_csv(INDEX_PATH, low_memory=False)

    # Assume exact columns and values are correct
    for _, req in user_df.iterrows():
        matches = idx_df.loc[(idx_df['cik'] == req['cik']) & (idx_df['fy'] == req['year']) & (idx_df['fp'] == req['quarter'])]
        for _, m in matches.iterrows():
            base = f"CIK{m['cik']}_{m.get('form','Filing')}_{m['fy']}{m['fp']}"
            safe = str(base).replace('/', '_').replace('\\', '_').replace(':', '_').replace(' ', '_')
            out_path = os.path.join(OUT_DIR, safe)
            # Save both as .txt if present
            if pd.notna(m.get('txt_url')):
                _download(str(m['txt_url']), os.path.join(out_path, 'filing_txt.txt'))
            if pd.notna(m.get('html_url')):
                _download(str(m['html_url']), os.path.join(out_path, 'filing_htm.txt'))


if __name__ == "__main__":
    main()
