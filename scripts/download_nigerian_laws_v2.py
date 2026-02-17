import requests
import os

def download_file(url, folder, filename):
    local_path = os.path.join(folder, filename)
    if os.path.exists(local_path):
        print(f"Skipping {filename}, already exists.")
        return
    
    print(f"Downloading {filename} from {url}...")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded {filename}.")
    except Exception as e:
        print(f"Failed to download {filename}: {e}")

def main():
    folder = "legal_ai/data/nigeria_laws"
    os.makedirs(folder, exist_ok=True)
    
    laws = [
        {
            "name": "Constitution_1999_As_Amended_2023.pdf",
            "url": "https://www.fao.org/faolex/results/details/en/c/LEX-FAOC127413/" # Note: This is a detail page, I need the actual PDF link if possible, or fallback to PLAC
        },
        {
            "name": "CAMA_2020.pdf",
            "url": "https://nipc.gov.ng/wp-content/uploads/2020/12/COMPANIES-AND-ALLIED-MATTERS-ACT-2020.pdf"
        },
        {
            "name": "Evidence_Act_As_Amended.pdf",
            "url": "https://placng.org/i/wp-content/uploads/2019/12/Evidence-Act-2011.pdf"
        }
    ]
    
    # Correction for Constitution link from PLAC (Direct PDF)
    laws[0]["url"] = "https://placng.org/i/wp-content/uploads/2019/12/Constitution-of-the-Federal-Republic-of-Nigeria-1999-as-Amended.pdf"

    for law in laws:
        download_file(law["url"], folder, law["name"])

if __name__ == "__main__":
    main()
