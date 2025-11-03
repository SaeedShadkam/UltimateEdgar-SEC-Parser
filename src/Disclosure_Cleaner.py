import re
import requests
from bs4 import BeautifulSoup
import time
from Levenshtein import distance as levenshtein_distance
import numpy as np
import pandas as pd
import random
import time
import sys
import pickle
import os
from src.edgar_classes import Official_Items, Official_Items_10K, Official_Items_important_words, Official_Items_important_words_10K, Disclosure, Disclosure_10K, paragraph_splitter


number_of_words = 400 #number of words per paragraph after splitting
user_api = 'Example Contact (email@example.com)'


def main():
    sys.setrecursionlimit(int(sys.getrecursionlimit() * 1.5)) #15000 causes crashes in str(soup)

    list_of_disclosures = pd.read_csv('src/ListofDisclosurestoParse.csv')
    number_of_files = len(list_of_disclosures)
    disclosures_database = pd.read_csv('src/Financial Statement Dataset/edgar_sub_database.csv', low_memory=False)

    list_of_disclosures = pd.merge(
        list_of_disclosures,
        disclosures_database,
        left_on=['CIK', 'Year', 'Quarter'],
        right_on=['cik', 'fy', 'fp'],
        how='left'
    )

    # Ensure output directory exists
    os.makedirs('src/output', exist_ok=True)

    Cursed_disclosures = []

    for rn in range(number_of_files):
        print(f'Processing file {rn+1} of {number_of_files}')
        try:
            row = list_of_disclosures.iloc[rn, :]
            if row['form'] == '10-Q':
                disclosure = Disclosure.Initializer(row[['cik', 'txt_url', 'html_url', 'name', 'form', 'filed']], User_Api=user_api)
            else:
                disclosure = Disclosure_10K.Initializer(row[['cik', 'txt_url', 'html_url', 'name', 'form', 'filed']], User_Api=user_api)

            disclosure.Load()
            print(f'file {rn+1} was successfully loaded using the API')
            disclosure.debug = False
            disclosure.Remove_Tables()
            disclosure.debug = False
            disclosure.Section_Finder_html()
            disclosure.debug = False
            disclosure.Section_text_Finder()
            disclosure_processed = {}
            for i in range(len(disclosure.True_Items)-1):
                disclosure_processed[disclosure.True_Items[i]] = disclosure.sections_text[i]

            for key in disclosure_processed.keys():
                disclosure_processed[key] = paragraph_splitter(disclosure_processed[key], number_of_words)

            # Save as CIK_Year_Quarter.pkl
            cik_str = str(int(row['CIK'])) if not pd.isna(row['CIK']) else 'NA'
            year_str = str(int(row['Year'])) if not pd.isna(row['Year']) else 'NA'
            quarter_str = str(row['Quarter']) if not pd.isna(row['Quarter']) else 'NA'
            out_name = f"{cik_str}_{year_str}_{quarter_str}.pkl"
            with open(os.path.join('src', 'output', out_name), "wb") as h:
                pickle.dump(disclosure_processed, h)
            print(f'File {rn+1} was successfully processed.')
            print("=" * 50)
        except Exception as e:
            print(e)
            Cursed_disclosures.append(1)
            a = {}
            # Save empty object with same naming scheme
            try:
                cik_str = str(int(row['CIK'])) if not pd.isna(row['CIK']) else 'NA'
                year_str = str(int(row['Year'])) if not pd.isna(row['Year']) else 'NA'
                quarter_str = str(row['Quarter']) if not pd.isna(row['Quarter']) else 'NA'
                out_name = f"{cik_str}_{year_str}_{quarter_str}.pkl"
            except Exception:
                out_name = f"row_{rn+1}.pkl"
            with open(os.path.join('src', 'output', out_name), "wb") as h:
                pickle.dump(a, h)
            print(f'File {rn+1} was skipped.')


if __name__ == "__main__":
    main()



