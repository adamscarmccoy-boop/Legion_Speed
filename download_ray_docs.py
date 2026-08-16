import urllib.request
import urllib.parse
import re
import os
import ssl
from bs4 import BeautifulSoup

def clean_html(html):
    """Clean HTML tags and extract readable text."""
    soup = BeautifulSoup(html, "html.parser")
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.decompose()
    # Get text
    text = soup.get_text(separator="\n")
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)
    return text

def download_page(url, filename):
    """Download a single URL and save as clean text."""
    print(f"Downloading: {url}...")
    try:
        # Avoid SSL certificate errors on local machines
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, context=ctx) as response:
            html = response.read()
            text = clean_html(html)
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"  -> Saved to {filename}")
            return True
    except Exception as e:
        print(f"  -> Error downloading {url}: {e}")
        return False

def main():
    docs_dir = r"C:\WEB CASE STUDY\docs"
    os.makedirs(docs_dir, exist_ok=True)
    
    # Target some main Ray documentation entrypoints
    urls = {
        "ray_data_intro.txt": "https://docs.ray.io/en/latest/data/data.html",
        "ray_data_key_concepts.txt": "https://docs.ray.io/en/latest/data/key-concepts.html",
        "ray_core_intro.txt": "https://docs.ray.io/en/latest/ray-core/walkthrough.html",
        "ray_serve_intro.txt": "https://docs.ray.io/en/latest/serve/index.html",
        "ray_serve_key_concepts.txt": "https://docs.ray.io/en/latest/serve/key-concepts.html",
        "ray_train_intro.txt": "https://docs.ray.io/en/latest/train/train.html",
        "ray_rllib_intro.txt": "https://docs.ray.io/en/latest/rllib/index.html"
    }
    
    print("=== Ray Documentation Downloader ===")
    success_count = 0
    for name, url in urls.items():
        filepath = os.path.join(docs_dir, name)
        if download_page(url, filepath):
            success_count += 1
            
    print(f"\nSuccessfully downloaded {success_count}/{len(urls)} pages to {docs_dir}")

if __name__ == "__main__":
    main()
