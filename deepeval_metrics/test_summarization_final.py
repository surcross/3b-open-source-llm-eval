"""
Test faithfulness in LLM summarization responses.
This script retrieves summaries from MongoDB and evaluates them using
DeepEval's FaithfulnessMetric to detect unfaithful content.
"""

from pymongo import MongoClient
from deepeval.metrics import SummarizationMetric
from deepeval.test_case import LLMTestCase
import os
import sys
import argparse

# Add parent directory to Python path
sys.path.append('/home/ks/Desktop/project/test_llm')
from config import DEFAULT_MODEL

# Function to get test cases from MongoDB
def get_test_cases(model):
    client = MongoClient('mongodb://localhost:27018/')
    db = client['rag_evaluation']
    collection = db['summarization_tests']
    
    # Convert model name to MongoDB-friendly format
    safe_model_name = model.replace(':', '_').replace('.', '_')
    answer_field = f"llm_answer_{safe_model_name}"
    score_field = f"summarization_score_{safe_model_name}"
    
    # Build a list of test cases
    test_cases = []
    for doc in collection.find():
        # Skip test cases that have already been evaluated for this model
        if score_field in doc:
            continue
            
        # Skip test cases without answers for this model
        if not doc.get(answer_field):
            continue
            
        test_cases.append({
            "input": doc.get("input", "Summarize the following text"),
            "context": doc["context"],
            "_id": doc["_id"],
            "model": model,
            "safe_model_name": safe_model_name
        })
    
    print(f"Found {len(test_cases)} test cases that need summarization evaluation for model: {model}")
    
    # Print a sample document structure
    if test_cases:
        print(f"Sample test case structure: {test_cases[0]}")
    
    return test_cases

# Evaluate summarization using deepeval with Ollama model
def evaluate_summarization(test_case, model):
    # Get model-specific answer field from MongoDB
    client = MongoClient('mongodb://localhost:27018/')
    db = client['rag_evaluation']
    collection = db['summarization_tests']
    
    # Convert model name to MongoDB-friendly format
    safe_model_name = model.replace(':', '_').replace('.', '_')
    answer_field = f"llm_answer_{safe_model_name}"
    
    # Retrieve the full document to get the answer
    doc = collection.find_one({"_id": test_case["_id"]})
    if not doc or not doc.get(answer_field):
        print(f"No answer found for {answer_field}")
        return 0.0, "No answer available for evaluation", False
    
    # Create the test case for evaluation
    llm_test_case = LLMTestCase(
        input=test_case["input"],
        actual_output=doc[answer_field],
        retrieval_context=[test_case["context"]]
    )
    metric = SummarizationMetric(threshold=0.7)
    try:
        metric.measure(llm_test_case)
        return metric.score, metric.reason, True
    except Exception as e:
        print(f"Error evaluating summarization: {e}")
        return 0.0, f"Error evaluating: {str(e)}", False

# Save results back to MongoDB
def save_results(test_id, summarization_score, summarization_reason, model):
    client = MongoClient('mongodb://localhost:27018/')
    db = client['rag_evaluation']
    collection = db['summarization_tests']
    # Convert model name to MongoDB-friendly format
    safe_model_name = model.replace(':', '_').replace('.', '_')
    score_field = f"summarization_score_{safe_model_name}"
    reason_field = f"summarization_reason_{safe_model_name}"
    collection.update_one(
        {"_id": test_id},
        {"$set": {
            score_field: summarization_score,
            reason_field: summarization_reason
        }}
    )

# Main function
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Evaluate summarization for LLM answers')
    parser.add_argument('--model', type=str, default=DEFAULT_MODEL, 
                        help=f'Model to evaluate (default: {DEFAULT_MODEL})')
    args = parser.parse_args()
    
    print(f"Evaluating summarization for model: {args.model}")
    
    # Get test cases from MongoDB that need evaluation
    test_cases = get_test_cases(args.model)
    
    # Process each test case
    for i, test in enumerate(test_cases, 1):
        summarization_score, summarization_reason, success = evaluate_summarization(test, test['model'])
        print(f"\nTest Case {i}")
        print(f"Context: {test['context'][:100]}... (truncated)")
        
        # Get the actual answer directly from MongoDB using model name
        client = MongoClient('mongodb://localhost:27018/')
        db = client['rag_evaluation']
        collection = db['summarization_tests']
        safe_model_name = test['model'].replace(':', '_').replace('.', '_')
        answer_field = f"llm_answer_{safe_model_name}"
        full_doc = collection.find_one({"_id": test["_id"]})
        
        if full_doc and answer_field in full_doc:
            print(f"Summary: {full_doc[answer_field]}")
        else:
            print("Summary: [Not available]")
            
        print(f"Summarization Score: {summarization_score}")
        print(f"Summarization Reason: {summarization_reason}")
        
        if success:
            save_results(test["_id"], summarization_score, summarization_reason, test['model'])
        else:
            print("Skipping database update due to evaluation error")
