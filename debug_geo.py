import pandas as pd
import requests
import io
import gzip

def debug():
    url = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE108nnn/GSE108222/matrix/GSE108222_series_matrix.txt.gz"
    print(f"Downloading header of {url}...")
    # Just get first 1MB
    headers = {"Range": "bytes=0-1000000"} 
    # Partial download might not work with gzip stream comfortably, let's just DL it again, it's small.
    r = requests.get(url) 
    
    # Parse
    try:
        text = gzip.decompress(r.content).decode('utf-8', errors='replace')
    except:
        text = r.content.decode('utf-8', errors='replace')
        
    lines = text.split('\n')
    header_line = 0
    start_line = 0
    for i, line in enumerate(lines):
        if line.startswith('"ID_REF"'): header_line = i
        if line.startswith('!Series_matrix_table_begin'): start_line = i
        
    print(f"Header Line: {header_line}")
    data_io = io.StringIO('\n'.join(lines[header_line:start_line-1]))
    df = pd.read_csv(data_io, sep='\t', index_col=0)
    
    print("\nFirst 10 Index Values (IDs):")
    print(df.index[:10].tolist())
    
    print("\nLooking for 'POU5F1' or 'OCT4'...")
    matches = [i for i in df.index if 'POU5F1' in str(i).upper() or 'OCT4' in str(i).upper()]
    print(f"Matches found: {matches}")

if __name__ == "__main__":
    debug()
