from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
import json

model_path = r"C:\Users\samar\Notepad_GUI\final_3"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForTokenClassification.from_pretrained(model_path)
model.eval()  # set model to evaluation mode
from transformers import pipeline

ner_pipeline = pipeline("token-classification", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

def extract_and_append_entities(text, json_path="ner_tags.json"):
    entities = ner_pipeline(text)
    tag = ""
    tags = []
    for entity in entities:
        word = entity['word']
        if word.startswith("##"):
            tag = tag + word[2:]
        else:
            if tag: 
                tags.append(tag)
            tag = word
    tags.append(tag)
    tag_dict = {f"[[{tag}]]": tag for tag in tags if tag.strip()}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = {}
    # Update and save
    existing_data.update(tag_dict)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    print("🏷 Extracted and saved tags:", tag_dict)
    return tag_dict
