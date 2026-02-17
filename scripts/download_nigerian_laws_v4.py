import requests
import os

def download_file(url, folder, filename):
    local_path = os.path.join(folder, filename)
    print(f"Trying {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, stream=True, timeout=30, headers=headers)
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
    
    tasks = [
        {
            "name": "Constitution_1999.pdf",
            "urls": [
                "https://www.wipo.int/edocs/lexdocs/laws/en/ng/ng007en.pdf",
                "https://www.refworld.org/pdfid/3ae6b5424.pdf"
            ]
        },
        {
            "name": "CAMA_2020.pdf",
            "urls": [
                "https://investmentpolicy.unctad.org/investment-laws/laws/326/download/Nigeria_Companies%20and%20Allied%20Matters%20Act%202020.pdf",
                "https://cac.gov.ng/wp-content/uploads/2020/12/CAMA-ACT-2020.pdf"
            ]
        }
    ]

    for task in tasks:
        for url in task["urls"]:
            if download_file(url, folder, task["name"]):
                break

if __name__ == "__main__":
    main()
