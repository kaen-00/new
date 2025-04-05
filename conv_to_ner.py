import re
import json
import nltk
from nltk.tokenize import word_tokenize
from tqdm import tqdm

nltk.download("punkt")

def extract_entities_and_tokens(text):
    entity_spans = []
    clean_text = ""
    i = 0

    # Extract entities and track span positions
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

    tokens = word_tokenize(clean_text)
    labels = ["O"] * len(tokens)

    # Assign labels based on entity spans
    offset = 0
    for start, end in entity_spans:
        entity_tokens = word_tokenize(clean_text[start:end])
        for j, token in enumerate(entity_tokens):
            try:
                index = tokens.index(token, offset)
                labels[index] = "B-ENTITY" if j == 0 else "I-ENTITY"
                offset = index + 1
            except ValueError:
                continue

    return {"tokens": tokens, "labels": labels}

def process_file(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f_in, open(output_path, "w", encoding="utf-8") as f_out:
        for line in tqdm(f_in, desc="Generating NER dataset"):
            line = line.strip()
            if not line:
                continue
            try:
                result = extract_entities_and_tokens(line)
                if "B-ENTITY" in result["labels"]:  # only save if entities exist
                    json.dump(result, f_out)
                    f_out.write("\n")
            except Exception as e:
                print("Error:", e)
                continue

if __name__ == "__main__":
    input_file = "test_set.txt"  # file with [[wikilinks]]
    output_file = "test_set.jsonl"
    process_file(input_file, output_file)
