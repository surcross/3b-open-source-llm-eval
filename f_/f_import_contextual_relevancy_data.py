"""
Simple script to import data from Hugging Face's FaithEval dataset to MongoDB.
Stores 20 random samples with 'input' and 'context' fields.
"""
from datasets import load_dataset
import random
from pymongo import MongoClient
import time
import os

# Set proxy environment variables for Hugging Face connection
os.environ['http_proxy'] = 'http://127.0.0.1:7890/'
os.environ['https_proxy'] = 'http://127.0.0.1:7890/'

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27018/')
db = client['rag_evaluation']
collection = db['contextual_relevancy_tests']

# Load dataset directly now that proxy is configured
print("Loading FaithEval dataset...")
print(f"Using proxy: {os.environ.get('https_proxy')}")

# Load the dataset  load _dataset从外部引进来的模块,怪不得看起来这么短,这么牛逼.
# tmd这是整个读进来啊,以后可以考虑先保存到本地了. 主要是要加代理,可靠性太差.
# 还行,python会自行回收这个大东西.
dataset = load_dataset("Salesforce/FaithEval-counterfactual-v1.0", split="test")
print(f"Dataset loaded with {len(dataset)} samples")

# Show sample structure
if len(dataset) > 0:
    sample = dataset[0]
    print("\nSample data fields:")
#    for key in sample:
#        print(f"- {key}")
# I just want to know why you use dataset[0] instead of others. and I want to know, what is the value looks like. 
    for key, value in sample.items():
        print(f"- {key}: {value}")

# Get random sample indices
sample_size = min(50, len(dataset))
random_indices = random.sample(range(len(dataset)), sample_size) #主要是函数用的多,我见识少.
#这个random.sample 应该看成(random.sample) 它属于python标准库中的模块函数而不是方法.
#在给定范围内随机挑sample_size 个.

# Import samples to MongoDB
inserted_count = 0
for idx in random_indices:
    sample = dataset[idx]   #在读数据
    
    # Create document with required fields
    doc = {
        "input": sample["question"],
        "context": [sample["context"]]
    }
    
    # Insert into MongoDB 下面是一些格式.
    result = collection.insert_one(doc)   #函数好用爱用.
    if result.inserted_id:
        inserted_count += 1
        print(f"Inserted sample {inserted_count}: {doc['input'][:50]}...")

print(f"\nImport completed. Added {inserted_count} new test cases to MongoDB.")


#这个没加重复确认
