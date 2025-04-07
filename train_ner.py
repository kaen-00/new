import torch
from datasets import load_dataset
import evaluate
import numpy as np
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    DataCollatorForTokenClassification,
    TrainingArguments,
    Trainer
)

# Setup device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

# Step 1: Load the dataset
dataset = load_dataset("json", data_files="train_set.jsonl")

# Step 2: Define labels
label_list = ["O", "B-ENTITY", "I-ENTITY"]
label_to_id = {l: i for i, l in enumerate(label_list)}
id_to_label = {i: l for l, i in label_to_id.items()}

# Step 3: Load tokenizer and model
model = AutoModelForTokenClassification.from_pretrained("ner-model-final").to(device)
tokenizer = AutoTokenizer.from_pretrained("ner-model-final")

print("Model is on device:", next(model.parameters()).device)

# Step 4: Preprocessing
def preprocess(example):
    tokenized_inputs = tokenizer(
        example["tokens"],
        is_split_into_words=True,
        truncation=True,
        padding="max_length",
        max_length=128,
    )

    word_ids = tokenized_inputs.word_ids()
    label_ids = []
    for word_idx in word_ids:
        if word_idx is None:
            label_ids.append(-100)
        else:
            label_ids.append(label_to_id[example["labels"][word_idx]])

    tokenized_inputs["labels"] = label_ids
    return tokenized_inputs

tokenized_dataset = dataset.map(preprocess, batched=False)

# Step 5: Metric
metric = evaluate.load("seqeval")

def compute_metrics(eval_preds):
    predictions, labels = eval_preds
    predictions = np.argmax(predictions, axis=2)

    true_labels = [[id_to_label[l] for l in label if l != -100] for label in labels]
    true_preds = [
        [id_to_label[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    results = metric.compute(predictions=true_preds, references=true_labels)
    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"],
    }

# Step 6: Trainer setup
data_collator = DataCollatorForTokenClassification(tokenizer)

args = TrainingArguments(
    output_dir="./ner_model",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=10,
    weight_decay=0.01,
    logging_dir="./logs",
    report_to="none"
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["train"],
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# Step 7: Train the model
trainer.train()
trainer.save_model("./final_3")
tokenizer.save_pretrained("./final_3")