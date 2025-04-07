import spacy
from collections import defaultdict

# Load the English NLP pipeline
nlp = spacy.load("en_core_web_sm")

def lemmatize_phrase(phrase, nlp):
    """Lemmatize a phrase into a tuple of lemmas."""
    return tuple(token.lemma_.lower() for token in nlp(phrase))

def build_tag_lemma_map(tags, nlp):
    """Create a map of tag index to its lemmatized token tuple."""
    return {i: lemmatize_phrase(tag, nlp) for i, tag in enumerate(tags)}

def find_tags_in_paragraph(paragraph, tags):
    doc = nlp(paragraph)
    tag_lemmas = build_tag_lemma_map(tags, nlp)

    matched_indices = defaultdict(list)  # maps paragraph word indices to tag index

    # Turn the paragraph into a list of (lemma, original index)
    para_lemmas = [(token.lemma_.lower(), i) for i, token in enumerate(doc) if not token.is_space]

    for tag_idx, tag_lemma_seq in tag_lemmas.items():
        tag_len = len(tag_lemma_seq)

        for i in range(len(para_lemmas) - tag_len + 1):
            window = para_lemmas[i:i+tag_len]
            window_lemmas = tuple(w[0] for w in window)

            if window_lemmas == tag_lemma_seq:
                word_indices = [w[1] for w in window]
                for idx in word_indices:
                    matched_indices[idx].append(tag_idx)

    return dict(matched_indices)

tags = ["lirili larila", "ohio", "quantum theory", "ass hole"]
paragraph = "lirili larila proposed the ohios, including quantum theories and the study of ass holes."

matches = find_tags_in_paragraph(paragraph, tags)
print(matches)
