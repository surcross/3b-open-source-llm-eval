# Import the libraries we need
from pymongo import MongoClient  # For connecting to MongoDB database
import requests  # For making HTTP requests to Ollama
import re  # For regular expressions to clean up responses
import argparse  # For command line arguments
import sys  # For accessing script arguments
sys.path.append('/home/ks/Desktop/project/test_llm')  # Add parent directory to path
from config import DEFAULT_MODEL  # Import default model from config

# Step 1: Connect to MongoDB
# This creates a connection to the MongoDB running on your computer
client = MongoClient('mongodb://localhost:27018/')  # Connect to MongoDB at localhost
db = client['rag_evaluation']  # Select the 'rag_evaluation' database
collection = db['faithfulness_tests']  # Select the 'faithfulness_tests' collection

# Parse command line arguments  #属于是整了个类玩玩.
parser = argparse.ArgumentParser(description='Query LLM for faithfulness evaluation')
parser.add_argument('--model', type=str, default=DEFAULT_MODEL, help=f'Model to use (default: {DEFAULT_MODEL})')  #python是好文明
args = parser.parse_args()

# Display which model we're using
print(f"Using model: {args.model}")

# Step 2: Get questions from MongoDB that don't have llm_answer for the selected model yet
print("Getting faithfulness questions from database...")
questions = []  # Create an empty list to store our questions . #no need but good. i like this . 
for doc in collection.find():  # Loop through each document in the collection   
    # Field name for this model's answer - need to handle the model name correctly
    # MongoDB has issues with field names containing special characters
    # Convert deepseek-r1:1.5b to llm_answer_deepseek-r1_1_5b
    safe_model_name = args.model.replace(':', '_').replace('.', '_')
    model_answer_field = f"llm_answer_{safe_model_name}"   #为了赋值带变量的string 
    
    # Skip documents that already have an answer for this model
    if model_answer_field in doc and doc[model_answer_field]:
        continue
    
    # Add each question, its context, and document ID to our list
    questions.append({
        "_id": doc["_id"],        # The MongoDB document ID (needed for saving answers later)
        "question": doc["input"],  # The question is stored in the 'input' field
        "context": doc["context"]  # The context is stored in the 'context' field
    })

# Step 3: Process each question
print(f"Found {len(questions)} faithfulness questions to process")
for i, q in enumerate(questions, 1):  # Loop through questions with numbering starting at 1
    # Get the question text
    question = q["question"]
    
    # Format the context (it might be a list or a string) #ai考虑的是真的很细.
    if isinstance(q["context"], list):  # Check if context is a list
        context = " ".join(q["context"])  # Join list items with spaces
    else:
        context = q["context"]  # Use context as is
    
    # Display the question and context
    print(f"\n----- Question {i}/{len(questions)}: {question} -----")
    print(f"Context: {context}")
    
    # Step 4: Create the prompt for Ollama with clear instructions for faithfulness
    prompt = f"""Question: {question}
Context: {context}

Very important: Answer ONLY using information in the context above.
Do NOT add any details not explicitly mentioned in the context.
Stay faithful to the provided context and avoid making up information.
Keep your answer short and factual.

Answer:"""
    
    # Let the user know we're asking Ollama
    print("Asking Ollama...")
    
    # Step 5: Send request to Ollama
    try:
        # Send HTTP POST request to the Ollama API
        response = requests.post(
            "http://localhost:11434/api/generate",  # Ollama API URL
            json={
                "model": args.model,  # The model to use from command line args or default
                "prompt": prompt,  # Our question prompt
                "stream": False  # Get the full response at once, not streamed
            }
        )
        
        # Step 6: Process the response
        if response.status_code == 200:  # Check if request was successful
            # Get the response text from the JSON
            answer = response.json().get("response", "")
            
            # Step 7: Clean the answer (remove thinking sections)
            clean_answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)
            clean_answer = clean_answer.strip()  # Remove extra whitespace
            
            # Display the answer
            print("Answer:")
            print(clean_answer)
            
            # Step 8: Save the answer back to MongoDB with model-specific field name
            # MongoDB has issues with field names containing special characters
            # Convert deepseek-r1:1.5b to llm_answer_deepseek-r1_1_5b
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
            
    except Exception as e:
        # Handle any errors that might occur
        print(f"Error: {e}")
    
    # Print a separator line
    print("-" * 50)

# Print completion message
print(f"All faithfulness questions processed and saved to MongoDB using model {args.model}.")
#beautiful structure. it is wonderful.
