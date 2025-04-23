"""
Script to import data from Hugging Face's multilingual toxicity dataset to MongoDB.
Stores entries with 'input' field containing the text from the dataset.
"""
from datasets import load_dataset
import random
from pymongo import MongoClient
import os

# Set proxy environment variables for Hugging Face connection
os.environ['http_proxy'] = 'http://127.0.0.1:7890/'
os.environ['https_proxy'] = 'http://127.0.0.1:7890/'

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27018/')
db = client['rag_evaluation']
collection = db['toxicity_tests']

# Load dataset with proxy configured
print("Loading textdetox/multilingual_toxicity_dataset...")
print(f"Using proxy: {os.environ.get('https_proxy')}")

# Load the dataset
dataset = load_dataset("textdetox/multilingual_toxicity_dataset")

# Find out what splits are available
print(f"Available splits: {list(dataset.keys())}")

# Select the first available split
split_name = list(dataset.keys())[0]
print(f"Using split: {split_name}")
print(f"Dataset loaded with {len(dataset[split_name])} samples")

# Show sample structure
if len(dataset[split_name]) > 0:
    sample = dataset[split_name][0]
    print("\nSample data fields:")
    for key, value in sample.items():
        print(f"- {key}: {value}")

# Get random sample indices
sample_size = min(100, len(dataset[split_name]))
random_indices = random.sample(range(len(dataset[split_name])), sample_size)

# Import samples to MongoDB
inserted_count = 0
for idx in random_indices:
    sample = dataset[split_name][idx]
    
    # Create document with only the text field as input
    doc = {
        "input": sample["text"]
    }
    
    # Check if this exact text already exists in the database
    existing = collection.find_one({"input": doc["input"]})
    if existing:
        print(f"Skipping duplicate: {doc['input'][:50]}...")
        continue
    
    # Insert into MongoDB
    result = collection.insert_one(doc)
    if result.inserted_id:
        inserted_count += 1
        print(f"Inserted sample {inserted_count}: {doc['input'][:50]}...")

print(f"\nImport completed. Added {inserted_count} new toxicity test cases to MongoDB.")
