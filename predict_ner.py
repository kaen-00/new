from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import json
import os

# Load model and tokenizer
model_path = r"C:\Users\samar\Notepad_GUI\final_3"

tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
model = AutoModelForTokenClassification.from_pretrained(model_path, local_files_only=True)
model.eval()

# Use no aggregation to get raw tokens
ner_pipeline = pipeline("token-classification", model=model, tokenizer=tokenizer, aggregation_strategy="none")

def predict_entities(text):
    results = ner_pipeline(text)

    print("\n🔍 Raw model output:")
    for r in results:
        print(f"{r['word']:<15} | {r['entity']} | score: {r['score']:.2f}")

    tags = []
    current_tag = ""

    for i, token in enumerate(results):
        word = token["word"]
        label = token["entity"]

        if label != "O":
            if word.startswith("##"):
                current_tag += word[2:]
            else:
                if current_tag:
                    tags.append(current_tag)
                current_tag = word
        else:
            if current_tag:
                tags.append(current_tag)
                current_tag = ""

    if current_tag:
        tags.append(current_tag)

    new_tags = {}
    for tag in tags:
        clean = tag.replace("##", "").strip()
        if clean:
            new_tags[f"[[{clean}]]"] = clean

    print("\n✅ New extracted tags:")
    for k in new_tags:
        print(f"{k} -> {new_tags[k]}")

    return new_tags

# Input text
text = """Pharmacology is the branch of medicine concerned with the uses, effects, and modes of action of drugs."""

# Predict
new_entities = predict_entities(text)

# Path to file
json_path = "ner_tags.json"

# Load existing if available
if os.path.exists(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading existing JSON: {e}")
        existing_data = {}
else:
    existing_data = {}

# Merge
existing_data.update(new_entities)

# Save back
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(existing_data, f, indent=2, ensure_ascii=False)

print(f"\n✅ Tags appended and saved to {json_path}")
