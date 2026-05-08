
import requests
import os

def find_vascular_url():
    collection_id = "c407a8df-6f9a-4cce-am6c-94132170364f"
    api_url = f"https://api.cellxgene.cziscience.com/curation/v1/collections/{collection_id}"
    
    response = requests.get(api_url)
    data = response.json()
    
    for dataset in data.get('datasets', []):
        if "Vascular" in dataset.get('title', ''):
            print(f"FOUND: {dataset.get('title')}")
            for asset in dataset.get('assets', []):
                if asset.get('filetype') == 'H5AD':
                    print(f"URL: {asset.get('presigned_url')}")
                    return asset.get('presigned_url')
    return None

if __name__ == "__main__":
    find_vascular_url()
