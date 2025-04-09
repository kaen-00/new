from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
model_path = "/home/kaen/dir1/final_2"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForTokenClassification.from_pretrained(model_path)
model.eval()  # set model to evaluation mode
from transformers import pipeline

ner_pipeline = pipeline("token-classification", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

def predict_entities(text):
    results = ner_pipeline(text)
    return results
text = "This definition of bandwidth is in contrast to the field of signal processing, wireless communications, modem data transmission, digital communications, and electronics,[citation needed] in which bandwidth is used to refer to analog signal bandwidth measured in hertz, meaning the frequency range between lowest and highest attainable frequency while meeting a well-defined impairment level in signal power. The actual bit rate that can be achieved depends not only on the signal bandwidth but also on the noise on the channel. "
entities = predict_entities(text)

for entity in entities:
    print(f"{entity['word']} -> {entity['entity_group']} (score: {entity['score']:.2f})")
