"""
Simple script to import data from Hugging Face's CDial-Bias dataset to MongoDB.
Stores limited bias-related questions (context=1) from the dataset.
"""
from datasets import load_dataset
from pymongo import MongoClient
import os
import random

# Set proxy environment variables for Hugging Face connection
os.environ['http_proxy'] = 'http://127.0.0.1:7890/'
os.environ['https_proxy'] = 'http://127.0.0.1:7890/'

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27018/')
db = client['rag_evaluation']
collection = db['bias_tests']

# Load dataset directly now that proxy is configured
print("Loading para-zhou/CDial-Bias dataset...")
print(f"Using proxy: {os.environ.get('https_proxy')}")

# Load the dataset
dataset = load_dataset("para-zhou/CDial-Bias")
print(f"Dataset loaded successfully")

# Show dataset structure
print(f"\nDataset contains {len(dataset['train'])} samples in train split")

# Show sample structure
if len(dataset['train']) > 0:
    sample = dataset['train'][0]
    print("\nSample data fields:")
    for key, value in sample.items():
        print(f"- {key}: {value}")

# Filter samples where context == 1
context_1_samples = [sample for sample in dataset['train'] if 'context' in sample and sample['context'] == 1]
print(f"Found {len(context_1_samples)} samples with context=1")

# Limit number of samples (similar to faitheval script)
sample_size = min(100, len(context_1_samples))
random_indices = random.sample(range(len(context_1_samples)), sample_size)
print(f"Selecting {sample_size} random samples to import")

# Import samples to MongoDB
inserted_count = 0
for idx in random_indices:
    sample = context_1_samples[idx]
    
    # Create document with required field
    doc = {
        "input": sample["q"]  # Store the 'q' field as 'input'
    }
    
    # Insert into MongoDB
    try:
        result = collection.insert_one(doc)
        if result.inserted_id:
            inserted_count += 1
            print(f"Inserted sample {inserted_count}: {doc['input'][:50]}...")
    except Exception as e_insert:
        print(f"Error inserting document: {e_insert}")

print(f"\nImport completed. Added {inserted_count} new bias test cases to MongoDB.")

# Note: Duplicate checking has not been implemented, similar to the faitheval script.


#没有加重复检测 目前没多大影响