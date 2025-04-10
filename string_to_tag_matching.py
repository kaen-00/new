import json
import spacy
import re
from collections import defaultdict
from pathlib import Path

nlp = spacy.load("en_core_web_sm")

def lemmatize_phrase(phrase, nlp):
    return tuple(token.lemma_.lower() for token in nlp(phrase))

def build_lemma_to_tag_map(tags, nlp):
    lemma_map = {}
    for tag in tags:
        lemma = lemmatize_phrase(tag, nlp)
        lemma_map[lemma] = tag
    return lemma_map

def find_and_replace_tags(text, json_path):
    json_path = Path(json_path)

    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            tags = json.load(f)
    else:
        tags = {}

    tag_values = list(tags.values())
    lemma_to_tag = build_lemma_to_tag_map(tag_values, nlp)

    # Step 1: Track all existing [[tag]] spans so we can skip them
    existing_links = [
        (m.start(), m.end()) for m in re.finditer(r'\[\[.*?\]\]', text)
    ]

    def is_inside_existing_link(start, end):
        return any(link_start <= start < link_end or link_start < end <= link_end for link_start, link_end in existing_links)

    doc = nlp(text)
    lemmas_with_indices = [
        (token.lemma_.lower(), token.idx, token.idx + len(token.text), token.text)
        for token in doc if not token.is_space
    ]

    replacements = []
    i = 0

    while i < len(lemmas_with_indices):
        match_found = False

        for tag_lemmas, canonical_tag in lemma_to_tag.items():
            tag_len = len(tag_lemmas)
            window = lemmas_with_indices[i:i + tag_len]

            if len(window) < tag_len:
                continue

            window_lemmas = tuple(w[0] for w in window)
            start = window[0][1]
            end = window[-1][2]

            if is_inside_existing_link(start, end):
                continue  # 🔒 Skip existing [[linked]] text

            if window_lemmas == tag_lemmas:
                matched_text = text[start:end]
                replacements.append((start, end, f"[[{canonical_tag}]]"))
                i += tag_len
                match_found = True
                break

        if not match_found:
            i += 1

    # Sort and apply replacements in reverse order
    replacements.sort(reverse=True)
    for start, end, replacement in replacements:
        text = text[:start] + replacement + text[end:]

    # Save updated tags to file (optional – or skip if you're not modifying tags)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(tags, f, indent=2)

    return text
