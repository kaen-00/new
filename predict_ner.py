from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import json
import os
print("✅ predict_ner.py was successfully imported.")
# Load model and pipeline once
model_path = r"C:\Users\samar\Notepad_GUI\final_3"
tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
model = AutoModelForTokenClassification.from_pretrained(model_path, local_files_only=True)
model.eval()
ner_pipeline = pipeline("token-classification", model=model, tokenizer=tokenizer, aggregation_strategy="none")

def extract_and_append_entities(text, json_path = r"C:\Users\samar\Notepad_GUI\ner_tags.json"):
    print("📥 Received text for NER:", repr(text))
    results = ner_pipeline(text)
    print("🧾 Raw NER results:", results)
    tags = []
    current_tag = ""

    for token in results:
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

    print("🏷 Extracted tags:", new_tags)

    # Load existing JSON
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load existing JSON: {e}")
            existing_data = {}
    else:
        existing_data = {}

    # Merge and save
    existing_data.update(new_tags)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Successfully saved to {json_path}")

    return list(new_tags.values())


