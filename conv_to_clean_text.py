import bz2
import re
import mwparserfromhell
import mwxml
import nltk
from typing import List

# Make sure the sentence tokenizer is downloaded
nltk.download("punkt")
from nltk.tokenize import sent_tokenize

def extract_plaintext(wikitext: str) -> List[str]:
    """
    Extract clean plaintext sentences from wikitext, preserving only:
    - Natural language text
    - Wikilinks in [[...]] format
    """
    if not wikitext:
        return []

    # First pass: remove complex wiki markup using regex
    patterns_to_remove = [
        r'\[\[Category:.*?\]\]',    # Categories
        r'\[\[File:.*?\]\]',        # Files
        r'\[\[Image:.*?\]\]',       # Images
        r'<ref.*?>.*?</ref>',       # References
        r'{{.*?}}',                 # Templates
        r'{\|.*?\|}',               # Tables
        r'<.*?>',                   # HTML tags
        r'==.*?==',                 # Headings
        r'\'\'\'.*?\'\'\'',         # Bold/italic
        r'\[\[.*?:.*?\]\]',         # Special namespace links
        r'\|\s*}}',                 # Template endings
        r'<!--.*?-->',              # Comments
        r'&[a-z]+;',                # HTML entities
        r'__[A-Z]+__',              # Magic words
    ]
    
    for pattern in patterns_to_remove:
        wikitext = re.sub(pattern, '', wikitext, flags=re.DOTALL)

    # Second pass: parse and preserve wikilinks
    wikicode = mwparserfromhell.parse(wikitext)
    for link in wikicode.filter_wikilinks():
        if not link.text:
            continue
        display_text = str(link.text or link.title).strip()
        if display_text:
            wikicode.replace(link, f"[[{display_text}]]")

    # Final clean text
    clean_text = str(wikicode)
    clean_text = ' '.join(clean_text.split())  # Normalize whitespace

    try:
        sentences = sent_tokenize(clean_text)
    except Exception as e:
        print("NLTK sent_tokenize failed:", e)
        # Fallback to regex-based sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', clean_text)

    # Filter sentences
    final_sentences = []
    for s in sentences:
        s = s.strip()
        if (
            re.search(r'[a-zA-Z]', s) and
            len(s.split()) >= 3 and
            10 <= len(s) <= 200 and
            not s.startswith(('|', '!', '{', '}', '[', ']'))
        ):
            final_sentences.append(s)

    return final_sentences

def process_dump(input_file: str, output_file: str):
    """Process the XML dump and write clean sentences to output_file."""
    dump = mwxml.Dump.from_file(bz2.open(input_file))

    with open(output_file, "w", encoding="utf-8") as f_out:
        for i, page in enumerate(dump):
            if page.namespace != 0:
                continue

            for revision in page:
                if not revision.text:
                    continue

                try:
                    sentences = extract_plaintext(revision.text)
                    for sent in sentences:
                        f_out.write(sent + "\n")

                    if i % 100 == 0:
                        print(f"Processed {i} pages... Last: {page.title}")

                except Exception as e:
                    print(f"Skipped page {page.id} ({page.title}): {str(e)}")

if __name__ == "__main__":
    input_file = "enwiki-latest-pages-articles-multistream25.xml-p57025656p58525655.bz2"
    output_file = "test_set.txt"
    process_dump(input_file, output_file)
