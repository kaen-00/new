#BEFORE RUNNING THIS MAKE SURE ALL CHARACTERS LIKE ===== ARENT THERE AND THAT [[]] ARE SPACE SEPAPRATED FROM ADJACENT WORDS 

import re
import json
from tqdm import tqdm
import nltk
from nltk.tokenize import sent_tokenize

nltk.download("punkt")

def extract_entities_and_tokens(text):
    entity_spans = []
    clean_text = ""
    i = 0

    # Extract [[entity]] markup and build clean_text
    while i < len(text):
        if text[i:i+2] == "[[":
            end = text.find("]]", i)
            if end == -1:
                break
            entity = text[i+2:end]
            entity_spans.append((len(clean_text), len(clean_text) + len(entity)))
            clean_text += entity
            i = end + 2
        else:
            clean_text += text[i]
            i += 1

    # Tokenize using regex that preserves hyphenated words
    token_pattern = re.compile(r'\b\w+(?:-\w+)*\b|[.,!?;]')
    tokens = []
    token_positions = []

    for match in token_pattern.finditer(clean_text):
        tokens.append(match.group())
        token_positions.append((match.start(), match.end()))

    labels = ["O"] * len(tokens)

    # Assign B-ENTITY / I-ENTITY labels
    for start, end in entity_spans:
        began = False
        for i, (tok_start, tok_end) in enumerate(token_positions):
            if tok_end <= start:
                continue
            if tok_start >= end:
                break
            if tok_start >= start and tok_end <= end:
                labels[i] = "B-ENTITY" if not began else "I-ENTITY"
                began = True

    return {"tokens": tokens, "labels": labels}

def process_file(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f_in, open(output_path, "w", encoding="utf-8") as f_out:
        full_text = f_in.read()
        sentences = sent_tokenize(full_text)

        for i in tqdm(range(0, len(sentences), 4), desc="Generating NER dataset"):
            chunk = " ".join(sentences[i:i+4])
            if not chunk.strip():
                continue
            try:
                result = extract_entities_and_tokens(chunk)
                if "B-ENTITY" in result["labels"]:
                    json.dump(result, f_out)
                    f_out.write("\n")
            except Exception as e:
                print("Error:", e)
                continue

if __name__ == "__main__":
    input_file = "/home/kaen/dir1/cleaned_paragraphs_20250406_111332.txt"
    output_file = "train_set.jsonl"
    process_file(input_file, output_file)
