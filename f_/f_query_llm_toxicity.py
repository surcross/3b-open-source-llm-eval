# Import the libraries we need
from pymongo import MongoClient  # For connecting to MongoDB database
import requests  # For making HTTP requests to Ollama
import argparse  # For command line arguments
import sys  # For accessing script arguments
sys.path.append('/home/ks/Desktop/project/test_llm')  # Add parent directory to path
from config import DEFAULT_MODEL  # Import default model from config

# Step 1: Connect to MongoDB
# This creates a connection to the MongoDB running on your computer
client = MongoClient('mongodb://localhost:27018/')  # Connect to MongoDB at localhost
db = client['rag_evaluation']  # Select the 'rag_evaluation' database
collection = db['toxicity_tests']  # Select the 'toxicity_tests' collection

# Parse command line arguments
parser = argparse.ArgumentParser(description='Query LLM for toxicity evaluation')
parser.add_argument('--model', type=str, default=DEFAULT_MODEL, help=f'Model to use (default: {DEFAULT_MODEL})')
args = parser.parse_args()

# Display which model we're using
print(f"Using model: {args.model}")

# Step 2: Get inputs from MongoDB that don't have llm_answer for the selected model yet
print("Getting toxicity inputs from database...")
inputs = []  # Create an empty list to store our inputs
for doc in collection.find():  # Loop through each document in the collection
    # Field name for this model's answer - handle the model name correctly
    # MongoDB has issues with field names containing special characters
    safe_model_name = args.model.replace(':', '_').replace('.', '_')
    model_answer_field = f"llm_answer_{safe_model_name}"
    
    # Skip documents that already have an answer for this model
    if model_answer_field in doc and doc[model_answer_field]:
        continue
    
    # Add each input and document ID to our list
    inputs.append({
        "_id": doc["_id"],        # The MongoDB document ID (needed for saving answers later)
        "input": doc["input"]     # The input text is stored in the 'input' field
    })

# Step 3: Process each input
print(f"Found {len(inputs)} toxicity test inputs to process")
for i, q in enumerate(inputs, 1):  # Loop through inputs with numbering starting at 1
    # Get the input text
    input_text = q["input"]
    
    # Display the input
    print(f"\n----- Input {i}/{len(inputs)} -----")
    print(f"Input: {input_text[:100]}..." if len(input_text) > 100 else f"Input: {input_text}")  # Show first 100 chars
    
    # Step 4: Use the input text directly as the prompt
    prompt = input_text
    
    # Let the user know we're asking Ollama
    print("Asking Ollama...")
    
    # Step 5: Send request to Ollama
    try:
        # Send HTTP POST request to the Ollama API
        response = requests.post(
            "http://localhost:11434/api/generate",  # Ollama API URL
            json={
                "model": args.model,  # The model to use from command line args or default
                "prompt": prompt,     # Our prompt
                "stream": False       # Get the full response at once, not streamed
            }
        )
        
        # Step 6: Process the response
        if response.status_code == 200:  # Check if request was successful
            # Get the response text from the JSON
            answer = response.json().get("response", "")
            
            # Step 7: Clean the answer (remove special characters while preserving toxicity)
            # Remove special characters like <think> tags while preserving potentially toxic content
            import re
            clean_answer = answer.strip()  # Remove extra whitespace
            clean_answer = re.sub(r'<[^>]*>', '', clean_answer)  # Remove HTML-like tags such as <think>
            clean_answer = clean_answer.strip()  # Remove any whitespace created by the cleaning
            
            # Display the answer
            print("Answer:")
            print(clean_answer[:200] + "..." if len(clean_answer) > 200 else clean_answer)
            
            # Step 8: Save the answer back to MongoDB with model-specific field name
            safe_model_name = args.model.replace(':', '_').replace('.', '_')
            model_answer_field = f"llm_answer_{safe_model_name}"
            collection.update_one(
                {"_id": q["_id"]},  # Find the document by its ID
                {"$set": {model_answer_field: clean_answer}}  # Add/update the model-specific answer field
            )
            print("✓ Answer saved to database")
            
        else:
            # Display error if request failed
            print(f"Error: HTTP status code {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        # Handle any errors that might occur
        print(f"Error: {e}")
    
    # Print a separator line
    print("-" * 50)

# Print completion message
print(f"All toxicity test inputs processed and saved to MongoDB using model {args.model}.")
