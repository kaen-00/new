from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
model_path = "/home/kaen/dir1/ner-model-final_2"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForTokenClassification.from_pretrained(model_path)
model.eval()  # set model to evaluation mode
from transformers import pipeline

ner_pipeline = pipeline("token-classification", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

def predict_entities(text):
    results = ner_pipeline(text)
    return results
text = "South Korea's Constitutional Court removes Yoon Suk Yeol "
entities = predict_entities(text)

for entity in entities:
    print(f"{entity['word']} -> {entity['entity_group']} (score: {entity['score']:.2f})")
