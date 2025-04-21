from pymongo import MongoClient
from deepeval.metrics.hallucination.hallucination import HallucinationMetric
from deepeval.test_case import LLMTestCase
import os
import sys
import argparse

# Add parent directory to path to import config
sys.path.append('/home/ks/Desktop/project/test_llm')
from config import DEFAULT_MODEL

# Function to get test cases from MongoDB
def get_test_cases(model):
    client = MongoClient('mongodb://localhost:27018/')
    db = client['rag_evaluation']
    collection = db['hallucination_tests']
    
    # Convert model name to MongoDB-friendly format
    safe_model_name = model.replace(':', '_').replace('.', '_')
    answer_field = f"llm_answer_{safe_model_name}"
    score_field = f"hallucination_score_{safe_model_name}"
    
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
            "input": doc["input"],
            "context": doc["context"],
            "llm_answer": doc.get(answer_field, ""),
            "_id": doc["_id"],
            "model": model,
            "safe_model_name": safe_model_name
        })
    
    print(f"Found {len(test_cases)} test cases that need hallucination evaluation for model: {model}")
    
    # Print a sample document structure
    if test_cases:
        print(f"Sample document structure: {test_cases[0]}")
    
    return test_cases


# Evaluate hallucination using deepeval with Ollama model
def evaluate_hallucination(test_case, model):
    # Create a deepeval LLMTestCase
    llm_test_case = LLMTestCase(
        input=test_case["input"],
        actual_output=test_case["llm_answer"],
        context=test_case["context"]
    )
    
    # Create the hallucination metric with Ollama model
    # DeepEval will use the model set with `deepeval set-ollama` command
    metric = HallucinationMetric(threshold=0.5)
    
    try:
        # Measure hallucination
        metric.measure(llm_test_case)
        return metric.score, metric.reason            # 这种带不带(,) 都属于tuple,不可变的sequence.
    except Exception as e:
        print(f"Error evaluating hallucination: {e}")
        return 0.5, f"Error evaluating: {str(e)}"

# Save results back to MongoDB
def save_results(test_id, hallucination_score, hallucination_reason, model):
    client = MongoClient('mongodb://localhost:27018/')
    db = client['rag_evaluation']
    collection = db['hallucination_tests']
    
    # Convert model name to MongoDB-friendly format
    safe_model_name = model.replace(':', '_').replace('.', '_')
    score_field = f"hallucination_score_{safe_model_name}"
    reason_field = f"hallucination_reason_{safe_model_name}"
    
    # Update the document with the evaluation results
    collection.update_one(
        {"_id": test_id},
        {"$set": {
            score_field: hallucination_score,
            reason_field: hallucination_reason
        }}
    )

# Main function
if __name__ == "__main__":
    # First, make sure you've set your Ollama model with the CLI command:
    # deepeval set-ollama gemma3:4b
    # If you haven't done this yet, you'll need to run it in your terminal first
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Evaluate hallucination for LLM answers')
    parser.add_argument('--model', type=str, default=DEFAULT_MODEL, 
                        help=f'Model to evaluate (default: {DEFAULT_MODEL})')
    args = parser.parse_args()
    
    print(f"Evaluating hallucination for model: {args.model}")
    
    # Get test cases from MongoDB
    test_cases = get_test_cases(args.model)
    
    # Process each test case
    for i, test in enumerate(test_cases, 1):
        
        # Evaluate hallucination using deepeval    tuple 类型的赋值方式
        hallucination_score, hallucination_reason = evaluate_hallucination(test, test['model'])
        
        # Print results
        print(f"\nTest Case {i}: {test['input']}")
        print(f"Context: {test['context']}")
        print(f"Answer: {test['llm_answer']}")
        print(f"Hallucination Score: {hallucination_score}")
        print(f"Hallucination Reason: {hallucination_reason}")
        
        # Save results back to MongoDB
        save_results(test["_id"], hallucination_score, hallucination_reason, test['model'])
