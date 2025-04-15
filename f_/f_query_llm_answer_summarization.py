# Import necessary libraries
from pymongo import MongoClient
import requests
import re  # For regular expressions to clean up responses

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27018/')
db = client['rag_evaluation']  # Use the same database as hallucination example
collection = db['summarization_tests']  # Using summarization collection

# Get documents without llm_answer
print("Getting documents from database...")
questions = []
for doc in collection.find():
    # Skip if llm_answer already exists and is not empty
    if "llm_answer" in doc and doc["llm_answer"] and doc["llm_answer"].strip():
        continue
    
    # For summarization collection, there is just context and no input field
    questions.append({
        "_id": doc["_id"],
        "context": doc["context"]
    })

# Process each document
print(f"Found {len(questions)} documents to process")
for i, q in enumerate(questions, 1):
    # Format context (handle both list and string)
    if isinstance(q["context"], list):
        context = " ".join(q["context"])
    else:
        context = q["context"]
    
    print(f"\n----- Document {i}/{len(questions)} -----")
    
    # Create prompt for summarization
    prompt = f"""Context: {context}

Please provide a concise and accurate summary of the main points from the above context.

Summary:"""
    
    print("Querying Ollama...")
    
    try:
        # Send request to Ollama
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "deepseek-r1:1.5b",
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            # Get the response
            answer = response.json().get("response", "")
            
            # Clean the answer (remove thinking sections)
            # Remove anything between <think> and </think> tags
            clean_answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)
            clean_answer = clean_answer.strip()  # Remove extra whitespace
            
            # Display summary
            print(f"Summary: {clean_answer[:50]}..." if len(clean_answer) > 50 else f"Summary: {clean_answer}")
            
            # Save to MongoDB
            collection.update_one(
                {"_id": q["_id"]},
                {"$set": {"llm_answer": clean_answer}}
            )
            print("✓ Summary saved to database")
        else:
            print(f"Error: HTTP status code {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print("-" * 50)

print("All questions processed and summaries saved to MongoDB.")
