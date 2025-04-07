import hdbscan
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import numpy as np

def cluster_tags(tags, min_cluster_size=2):
    # Step 1: Embed the tags
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(tags)

    # Step 2: Cluster with HDBSCAN
    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric='euclidean')
    labels = clusterer.fit_predict(embeddings)

    # Step 3: Group tags by cluster
    clustered_tags = defaultdict(list)
    for tag, label in zip(tags, labels):
        if label != -1:  # ignore noise
            clustered_tags[label].append(tag)

    return clustered_tags

def extract_common_substring(tags):
    """Try to find a common substring or word-based overlap between tags."""
    if not tags:
        return ""

    # Tokenize tags
    tokenized = [tag.lower().split() for tag in tags]

    # Intersect tokens in order
    common_tokens = set(tokenized[0])
    for tokens in tokenized[1:]:
        common_tokens &= set(tokens)

    if common_tokens:
        return " ".join(sorted(common_tokens))
    
    # Fallback to shared prefix
    from os.path import commonprefix
    prefix = commonprefix(tags)
    return prefix.strip()

def generate_superset_tags(clustered_tags):
    superset_map = {}
    for cluster_id, tag_list in clustered_tags.items():
        summary = extract_common_substring(tag_list)
        if not summary:
            summary = tag_list[0]  # fallback to first tag
        superset_map[cluster_id] = {
            "superset_tag": summary,
            "members": tag_list
        }
    return superset_map

# === Example usage ===
if __name__ == "__main__":
    tags = [
        "Albert Einstein", "Einstein", "Stephen Hawking", "black holes",
        "quantum physics", "quantum theory", "quantum mechanics", "relativity", "general relativity",
        "neural networks", "deep learning", "machine learning", "transformer model", "transformer architecture"
    ]

    clustered = cluster_tags(tags)
    superset_tags = generate_superset_tags(clustered)

    for cluster_id, data in superset_tags.items():
        print(f"\n🌀 Cluster {cluster_id}")
        print(f"  🔹 Superset Tag: {data['superset_tag']}")
        print(f"  🔸 Members: {data['members']}")
