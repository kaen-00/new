from sentence_transformers import SentenceTransformer
import hdbscan
from keybert import KeyBERT
import spacy
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

# Load models
embedder = SentenceTransformer("all-mpnet-base-v2")
kw_model = KeyBERT(embedder)
nlp = spacy.load("en_core_web_sm")

def normalize_tag(tag):
    doc = nlp(tag.lower())
    return " ".join([token.lemma_ for token in doc if not token.is_punct])

def centroid_representative(tags, embeddings):
    centroid = np.mean(embeddings, axis=0)
    sims = cosine_similarity([centroid], embeddings)[0]
    return tags[np.argmax(sims)]

def generate_keyword_summary(tags):
    text = ". ".join(tags)
    keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 3), stop_words='english', top_n=1)
    return keywords[0][0] if keywords else centroid_representative(tags, embedder.encode(tags))

def cluster_tags(tag_list, min_cluster_size=2):
    normalized_tags = [normalize_tag(t) for t in tag_list]
    embeddings = embedder.encode(normalized_tags)

    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric='euclidean')
    cluster_labels = clusterer.fit_predict(embeddings)

    clusters = defaultdict(list)
    for tag, label in zip(tag_list, cluster_labels):
        if label != -1:  # Skip noise
            clusters[label].append(tag)

    cluster_summary = {}
    for label, tags in clusters.items():
        summary = generate_keyword_summary(tags)
        cluster_summary[summary] = tags

    return cluster_summary

# Example usage
tag_list = [
    "Albert Einstein", "Einstein", "Stephen Hawking", "black holes",
        "quantum physics", "quantum theory", "quantum mechanics", "relativity", "general relativity",
        "neural networks", "deep learning", "machine learning", "transformer model", "transformer architecture"
]

clusters = cluster_tags(tag_list)
for summary, tags in clusters.items():
    print(f"Superset: {summary}\n -> {tags}\n")
