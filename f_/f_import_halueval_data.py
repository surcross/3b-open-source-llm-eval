import json
import random
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27018/')
db = client['rag_evaluation']
collection = db['hallucination_tests']

# Path to the downloaded data
file_path = '/home/ks/Desktop/project/test_llm/qa_data.json'

# Load the data
try:
    # Try to handle both JSON and JSONL formats
    data = []
    with open(file_path, 'r') as f:
        # First try loading as a single JSON object/array
        try:
            data = json.load(f)    #这个时候就已经parse成python的dic了,每一行json都是一个单独的
            print(f"Successfully loaded JSON data with {len(data)} samples")
        except json.JSONDecodeError:
            # If that fails, try as JSONL (one JSON object per line)
            f.seek(0)  # Reset file pointer
            for line in f:
                line = line.strip() #这tm的在洗干净数据.
                if line:  # Skip empty lines
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"Error parsing line: {line[:50]}...")
            print(f"Successfully loaded JSONL data with {len(data)} samples")
    
    if not data:
        raise Exception("No valid data found in file")
    
except Exception as e:
    print(f"Error loading data: {e}")
    exit(1)

# Select 20 random samples
if len(data) > 20:
    random_samples = random.sample(data, 20)
    print(f"Selected 20 random samples out of {len(data)}")
else:
    random_samples = data
    print(f"Using all {len(data)} samples as there are fewer than 20")

# Transform and import to MongoDB
inserted_count = 0
for sample in random_samples:
    # Map HaluEval fields to our MongoDB structure
    transformed_sample = {
        "input": sample["question"],
        "context": [sample["knowledge"]]  # Wrap in list to match existing format
    }
    
    # Check if this question already exists to avoid duplicates  直接搜索查找,效果挺好. 
    existing = collection.find_one({"input": transformed_sample["input"]})
    if existing:
        print(f"Skipping duplicate question: {transformed_sample['input'][:50]}...")
        continue
    
    # Insert into MongoDB
    result = collection.insert_one(transformed_sample)
    if result.inserted_id:
        inserted_count += 1
        print(f"Inserted sample {inserted_count}: {transformed_sample['input'][:50]}...")

print(f"\nImport completed. Added {inserted_count} new test cases to MongoDB.")

# Print a sample of what's now in the database
print("\nSample of data in MongoDB:")
for doc in collection.find().limit(2):
    print(json.dumps(
        {k: (v if k != "_id" else str(v)) for k, v in doc.items()}, #因为_id在mongodb中是ObjectId,需要转换成字符串,不然json会坏掉的  
        #他娘的是从屁股后面开始读的, 先 for, 再k:v,
        indent=2  #让json每个key都缩进一下. 好读一点. 
    ))


#全部理解,爽到了嘿嘿嘿

