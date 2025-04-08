# Import needed library
from pymongo import MongoClient

# Connect to MongoDB
print("Connecting to MongoDB...")
client = MongoClient('mongodb://localhost:27018/')
db = client['rag_evaluation']
collection = db['faithfulness_tests']

# Remove llm_answer field from all documents
print("Removing llm_answer fields from faithfulness tests...")
result = collection.update_many(
    {"llm_answer": {"$exists": True}},  # Find all documents with llm_answer field
    {"$unset": {"llm_answer": ""}}      # Remove the llm_answer field
)

# Report results
print(f"Modified {result.modified_count} documents") #函数库牛逼
print("All llm_answer fields have been removed from faithfulness tests")
