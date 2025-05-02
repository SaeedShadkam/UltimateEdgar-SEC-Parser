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
from src.Class_Function import Official_Items, Official_Items_10K, Official_Items_important_words, Official_Items_important_words_10K, Disclosure, Disclosure_10K, paragraph_splitter

number_of_files = 10
number_of_words = 400
user_api ='saeed shadkam saeedshadkam70@gmail.com'
path_results = "/Users/shadkam/Desktop/FinLP_Pipeline"
path_resources ="/Users/shadkam/Desktop/FinLP_Pipeline/Resources"

sys.setrecursionlimit(int(sys.getrecursionlimit() * 1.5)) #15000 causes crashes in str(soup)
matched = pd.read_csv(f"{path_resources}/Disclosure_Transcript_Pairs.csv")


map_disclosure_transcriptid = {}
for _ in range(len(matched)):
    map_disclosure_transcriptid[matched.iloc[_, :]['TXTAddress']] = matched.iloc[_,:]['transcriptid']
with open(f"{path_resources}/map_disclosureTXTAddress_transcriptid.pkl", "wb") as h:
    pickle.dump(map_disclosure_transcriptid, h)


Old_HTMLs = []
Not_Well_Parsed = []
Cursed_disclosures = []

start_time = time.time()
#number_of_files = len(matched) #for the full sample
disclosures_processed = {}
for rn in range(1200, 1200+number_of_files):
    print(f'Starting: Transcript_id:{matched.iloc[rn,:]["transcriptid"]}')
    try:
        id = matched.iloc[rn,:]['transcriptid']
        if matched.iloc[rn,:]['FormType'] =='10-Q':
            disclosure = Disclosure.Initializer(matched.iloc[rn,:][['cik', 'TXTAddress', 'DisclosureAddress', 'CompanyName', 'FormType', 'DateFiled']], User_Api=user_api)
        else:
            disclosure = Disclosure_10K.Initializer(matched.iloc[rn,:][['cik', 'TXTAddress', 'DisclosureAddress', 'CompanyName', 'FormType', 'DateFiled']], User_Api=user_api)
        disclosure.Load()
        print(f'transcript {id} was successfully loaded using the API')
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

        disclosures_processed[id] = disclosure_processed
        with open(f"{path_resources}/{int(id)}.pkl", "wb") as h:
            pickle.dump(disclosure_processed, h)
        print(f'Done with: Transcript_id: {matched.iloc[rn,:]["transcriptid"]}')
    except Exception as e:
        print(e)
        disclosures_processed[matched.iloc[rn,:]['transcriptid']] = {}
        Cursed_disclosures.append(1)
        a = {}
        with open(f"{path_resources}/{int(matched.iloc[rn,:]['transcriptid'])}.pkl", "wb") as h:
            pickle.dump(a, h)
        print(f'Done with: Transcript_id: {matched.iloc[rn,:]["transcriptid"]}')


#with open(f"{path_resources}/disclosure_processed.pkl", "wb") as h:
 #   pickle.dump(disclosures_processed, h)

end_time = time.time()

Number_Parsed_Files = rn + 1 - len(Old_HTMLs) - len(Not_Well_Parsed) - len(Cursed_disclosures)
with open(f'{path_results}/Results.txt', 'w') as f:
    f.write('Stage 1: Cleaning the Disclosure\n')
    f.write(f'Required time was:{(end_time- start_time)/60} Mins\n')
    f.write(f'Out of {rn+1} files, {Number_Parsed_Files} where parsed, {len(Old_HTMLs)} were old htmls, {len(Not_Well_Parsed)} were not parsed, {len(Cursed_disclosures)} had unknown errors')



