from transformers import AutoTokenizer, AutoModelForTokenClassification
from datasets import load_dataset
import evaluate
import numpy as np

# Load model and tokenizer
model = AutoModelForTokenClassification.from_pretrained("ner-model-final")
tokenizer = AutoTokenizer.from_pretrained("ner-model-final")
label_list = ["O", "B-ENTITY", "I-ENTITY"]
label_to_id = {l: i for i, l in enumerate(label_list)}
id_to_label = {i: l for l, i in label_to_id.items()}

# Load dataset
dataset = load_dataset("json", data_files="test_set.jsonl")

# Preprocess
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

tokenized_dataset = dataset.map(preprocess)
from transformers import DataCollatorForTokenClassification, Trainer, TrainingArguments

metric = evaluate.load("seqeval")

def compute_metrics(eval_preds):
    predictions, labels = eval_preds
    predictions = np.argmax(predictions, axis=2)
    true_labels = [[id_to_label[l] for l in label if l != -100] for label in labels]
    true_preds = [[id_to_label[p] for (p, l) in zip(pred, label) if l != -100]
                  for pred, label in zip(predictions, labels)]
    results = metric.compute(predictions=true_preds, references=true_labels)
    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"],
    }

# Setup dummy training args
args = TrainingArguments(output_dir="./ner_eval_tmp", per_device_eval_batch_size=16)

# Use Trainer just for evaluation
trainer = Trainer(
    model=model,
    tokenizer=tokenizer,
    args=args,
    eval_dataset=tokenized_dataset["train"],
    data_collator=DataCollatorForTokenClassification(tokenizer),
    compute_metrics=compute_metrics,
)

# Run evaluation
metrics = trainer.evaluate()
print(metrics)
