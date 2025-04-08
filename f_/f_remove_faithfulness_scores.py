# Import MongoDB client
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27018/')
db = client['rag_evaluation']
collection = db['faithfulness_tests']

# Print initial status
print("Starting removal of faithfulness scores...")
print(f"Total documents in collection: {collection.count_documents({})}")
print(f"Documents with faithfulness_score: {collection.count_documents({'faithfulness_score': {'$exists': True}})}")

# Remove faithfulness_score and faithfulness_reason fields from all documents
result = collection.update_many(
    {'faithfulness_score': {'$exists': True}}, 
    {'$unset': {'faithfulness_score': "", 'faithfulness_reason': ""}}
)

# Print results
print(f"Documents modified: {result.modified_count}")
print("Removal complete!")

# End of file - This script removes faithfulness_score and faithfulness_reason fields from all documents in the faithfulness_tests collection
