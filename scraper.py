import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
import re

# List of Wikipedia page titles
urls = [
    "Feynman diagram",
    "Physics"
]

# Output file with timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f"cleaned_paragraphs_{timestamp}.txt"

def remove_references(text):
    """Remove bracketed references like [1], [23], etc."""
    return re.sub(r'\[\d+\]', '', text)

with open(output_file, 'w', encoding='utf-8') as f:
    for url in urls:
        try:
            full_url = f"https://en.wikipedia.org/wiki/{url}"
            response = requests.get(full_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove unwanted tags
            for tag in soup(['script', 'style', 'sup']):
                tag.decompose()

            paragraphs = soup.find_all('p')
            f.write(f"===== {url} =====\n\n")

            for p in paragraphs:
                line = ""
                for elem in p.children:
                    if elem.name == 'a':
                        anchor_text = elem.get_text(strip=True)
                        if anchor_text:
                            line += f"[[{anchor_text}]]"
                    elif isinstance(elem, str):
                        line += elem.strip()
                line = remove_references(line)
                if line.strip():
                    f.write(line + "\n\n")

            print(f"✅ Done: {url}")

        except Exception as e:
            print(f"❌ Failed: {url} — {e}")

print(f"\n📝 Output saved to: {output_file}")
