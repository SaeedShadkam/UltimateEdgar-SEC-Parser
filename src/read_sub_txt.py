"""Reading all sub.txt files (across quarter folders) and save a single CSV"""

import os
import pandas as pd


base_dir = os.path.join("src", "Financial Statement Dataset")
print(f"Reading sub.txt from immediate subfolders of: {base_dir}")

quarter_dirs = sorted(
    d for d in os.listdir(base_dir)
    if os.path.isdir(os.path.join(base_dir, d))
)
sub_paths = [os.path.join(base_dir, d, "sub.txt") for d in quarter_dirs]

print(f"Found {len(sub_paths)} folder(s). Reading...")

dfs = []
for p in sorted(sub_paths):
	print(f"  - {p}")
	dfs.append(pd.read_csv(p, sep='\t', low_memory=False))

df = pd.concat(dfs, ignore_index=True)

print(f"\nLoaded total {len(df)} rows and {len(df.columns)} columns")
print(f"Columns: {list(df.columns)}")

# Build HTML URL  using accession number without dashes and 'instance' name
if {'cik', 'adsh', 'instance'}.issubset(df.columns):
	adsh_nodash = df['adsh'].astype(str).str.replace('-', '', regex=False)
	df['html_url'] = (
		"https://www.sec.gov/Archives/edgar/data/" + df['cik'].astype(str)
		+ '/' + adsh_nodash + '/' + df['instance'].astype(str).str.replace('_', '.', regex=False)
	).str.replace('.xml', '', regex=False)
	
	# Ensure all URLs end with .htm
	df['html_url'] = df['html_url'].apply(lambda x: x if x.endswith('.htm') else x + '.htm')
	df['txt_url'] = (
		"https://www.sec.gov/Archives/edgar/data/" + df['cik'].astype(str)
		+ '/' + adsh_nodash + '/' + df['adsh'] + '.txt'
	)

	print(f"\nExample HTML URL:")
	print(df.iloc[0]['html_url'])

# Save combined CSV next to the dataset folder
output_csv = os.path.join("src", "Financial Statement Dataset", "edgar_sub_database.csv")
os.makedirs(os.path.dirname(output_csv), exist_ok=True)
df.to_csv(output_csv, index=False)
print(f"\nSaved combined CSV to {output_csv}")
