# Import necessary libraries
from pymongo import MongoClient
import requests
import re  # For regular expressions to clean up responses
import argparse  # For command line arguments
import sys  # For accessing script arguments
sys.path.append('/home/ks/Desktop/project/test_llm')  # Add parent directory to path
from config import DEFAULT_MODEL  # Import default model from config

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27018/')
db = client['rag_evaluation']  # Use the same database as hallucination example
collection = db['summarization_tests']  # Using summarization collection

# Parse command line arguments
parser = argparse.ArgumentParser(description='Query LLM for summarization evaluation')
parser.add_argument('--model', type=str, default=DEFAULT_MODEL, help=f'Model to use (default: {DEFAULT_MODEL})')
args = parser.parse_args()

# Display which model we're using
print(f"Using model: {args.model}")

# Get documents without llm_answer for the selected model
print("Getting documents from database...")
questions = []
for doc in collection.find():
    # Field name for this model's answer - need to handle special characters
    # MongoDB has issues with field names containing : and .
    safe_model_name = args.model.replace(':', '_').replace('.', '_')
    model_answer_field = f"llm_answer_{safe_model_name}"
    
    # Skip if model-specific answer already exists
    if model_answer_field in doc:
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
                "model": args.model,
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
            
            # Save to MongoDB with model-specific field name
            # MongoDB has issues with field names containing : and .
            safe_model_name = args.model.replace(':', '_').replace('.', '_')
            model_answer_field = f"llm_answer_{safe_model_name}"
            collection.update_one(
                {"_id": q["_id"]},
                {"$set": {model_answer_field: clean_answer}}
            )
            print("✓ Summary saved to database")
        else:
            print(f"Error: HTTP status code {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print("-" * 50)

print(f"All questions processed and summaries saved to MongoDB using model {args.model}.")
