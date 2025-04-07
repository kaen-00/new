from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
model_path = "/home/kaen/dir1/final_3"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForTokenClassification.from_pretrained(model_path)
model.eval()  # set model to evaluation mode
from transformers import pipeline

ner_pipeline = pipeline("token-classification", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

def predict_entities(text):
    results = ner_pipeline(text)
    return results
text = '''
In the scope of its subject, chemistry occupies an intermediate position between physics and biology.[7] It is sometimes called the central science because it provides a foundation for understanding both basic and applied scientific disciplines at a fundamental level.[8] For example, chemistry explains aspects of plant growth (botany), the formation of igneous rocks (geology), how atmospheric ozone is formed and how environmental pollutants are degraded (ecology), the properties of the soil on the Moon (cosmochemistry), how medications work (pharmacology), and how to collect DNA evidence at a crime scene (forensics).
'''
entities = predict_entities(text)

for entity in entities:
    print(f"{entity['word']} -> {entity['entity_group']} (score: {entity['score']:.2f})")
