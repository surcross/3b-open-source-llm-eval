"""
Import XSum summarization data to MongoDB.
This script loads the XSum dataset from Hugging Face, randomly selects 20 samples,
and saves them to the rag_summarization database in MongoDB.
Each sample contains a context (document text) field and an empty llm_answer field
that will be filled later.

The script also saves the dataset locally after the first download, so that
subsequent runs can load from the local file instead of downloading the large dataset again.
"""

from datasets import load_dataset
import random
from pymongo import MongoClient
import os
import json
import pickle

# Set proxy configuration for Hugging Face connection
os.environ['http_proxy'] = 'http://127.0.0.1:7890/'
os.environ['https_proxy'] = 'http://127.0.0.1:7890/'
os.environ['all_proxy'] = 'socks://127.0.0.1:7890/'

# Connect to MongoDB with the correct port
client = MongoClient('mongodb://localhost:27018/')
db = client['rag_evaluation']
collection = db['summarization_tests']

# Define the local data path
LOCAL_DATASET_PATH = './data/xsum_test.pkl'  #这个好啊,但感觉怪怪的..

try:
    # Check if we already have a local copy of the dataset
    if os.path.exists(LOCAL_DATASET_PATH):  #os.path 是在做兼容.  整体是确认路径是否存在. 路径包括了文件. 
        print(f"Loading dataset from local file: {LOCAL_DATASET_PATH}") #Python f-string (formatted string literal).
        with open(LOCAL_DATASET_PATH, 'rb') as f:   #r:open for reading; b: binary mode.
            print(f"Inside 'with' block, f is: {f}") # Print the file object f  #Inside 'with' block, f is: <_io.BufferedReader name='./data/xsum_test.pkl'>
            ds = pickle.load(f)                     #pickle python11 自带的库,然后反序列号. ds maybe is the deseriaze? 
        print(f"Loaded {len(ds)} samples from local dataset file")  

    else:
        # Make sure the data directory exists
        os.makedirs(os.path.dirname(LOCAL_DATASET_PATH), exist_ok=True) #ai命名老牛逼了. 
        
        # Download the dataset from Hugging Face
        print("Loading XSum dataset from Hugging Face...")
        print(f"Using proxy: {os.environ.get('https_proxy')}")
        ds = load_dataset("EdinburghNLP/xsum", split="test")  #这个dataset 是从hugging face 引入的包. 
        print(f"Loaded {len(ds)} samples from XSum dataset")
        
        # Save the dataset locally for future use
        print(f"Saving dataset to local file: {LOCAL_DATASET_PATH}")
        with open(LOCAL_DATASET_PATH, 'wb') as f:   #w: open for writting. b: binary mode.
            pickle.dump(ds, f)  #dump is for save,serialization; load is for using , deserialization . 
        print("Dataset saved successfully")
    
    # Get the total number of samples
    total_samples = len(ds)   #还是那个问题,我不知道ds长什么样. 
    
    # Set target number of documents we want in the collection
    TARGET_DOCUMENT_COUNT = 100
    
    # Loop until we reach the target count
    
    # Check current count in the collection
    current_count = collection.count_documents({})
    print(f"Collection currently contains {current_count} documents. Target is {TARGET_DOCUMENT_COUNT}.")
    
    while current_count < TARGET_DOCUMENT_COUNT:  # 看起来舒服多了. 
        # Get a random index
        random_idx = random.randrange(total_samples)
        sample = ds[random_idx]
        # No need to count attempts
        
        # Check if this document already exists in MongoDB (exact match on context field)
        existing_doc = collection.find_one({"context": sample["document"]})
        
        if existing_doc:
            # Document already exists, skip it
            print(f"Skipping duplicate document")
            continue
        
        # Create document with required fields - only include context
        document = {
            "context": sample["document"]  # The full document text
            # No empty llm_answer field - will be added when needed by query script
        }
        
        # Insert into MongoDB
        result = collection.insert_one(document)
        if result.inserted_id:
            print(f"Inserted document: First 50 chars: {sample['document'][:50]}...")
            
            # Update current count
            current_count = collection.count_documents({})
            print(f"Current collection count: {current_count}/{TARGET_DOCUMENT_COUNT}")
    
    print(f"\nImport completed. Target count reached or exceeded.")
    print(f"Collection now contains {current_count} documents.")
    
    # Print a sample document for verification
    print("\nSample document structure:")
    sample_doc = collection.find_one()
    if sample_doc:
        print(f"_id: {sample_doc['_id']}")
        print(f"context: {sample_doc['context'][:100]}... (truncated)")

        
except Exception as e:
    print(f"Error loading dataset or importing data: {e}")
    print("Please check your internet connection and proxy settings.")


#good