import requests
import os

def download_file(url, folder, filename):
    local_path = os.path.join(folder, filename)
    print(f"Trying {url}...")
    try:
        response = requests.get(url, stream=True, timeout=20)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Successfully downloaded {filename}!")
            return True
        else:
            print(f"Failed: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    return False

def main():
    folder = "legal_ai/data/nigeria_laws"
    os.makedirs(folder, exist_ok=True)
    
    # Try different PLAC date structures
    constitution_urls = [
        "https://placng.org/i/wp-content/uploads/2023/05/Constitution-of-the-Federal-Republic-of-Nigeria-1999-as-Amended.pdf",
        "https://placng.org/i/wp-content/uploads/2019/12/Constitution-of-the-Federal-Republic-of-Nigeria-1999-as-Amended.pdf"
    ]
    
    cama_urls = [
        "https://placng.org/i/wp-content/uploads/2020/08/COMPANIES-AND-ALLIED-MATTERS-ACT-2020.pdf",
        "https://nipc.gov.ng/wp-content/uploads/2020/12/COMPANIES-AND-ALLIED-MATTERS-ACT-2020.pdf"
    ]

    for url in constitution_urls:
        if download_file(url, folder, "Constitution_1999.pdf"):
            break

    for url in cama_urls:
        if download_file(url, folder, "CAMA_2020.pdf"):
            break

if __name__ == "__main__":
    main()
