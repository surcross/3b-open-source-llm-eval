from pymongo import MongoClient
from bson import ObjectId
import json
import sys
import argparse
from deepeval.metrics import ContextualRelevancyMetric
from deepeval.test_case import LLMTestCase

# Add parent directory to path to import config
sys.path.append('/home/ks/Desktop/project/test_llm')
from config import DEFAULT_MODEL

# Custom JSON encoder to handle MongoDB ObjectId
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

# Get test cases from MongoDB
def get_test_cases(model):
    client = MongoClient('mongodb://localhost:27018/')
    db = client['rag_evaluation']
    collection = db['contextual_relevancy_tests']
    
    # Convert model name to MongoDB-friendly format
    safe_model_name = model.replace(':', '_').replace('.', '_')
    answer_field = f"llm_answer_{safe_model_name}"
    score_field = f"contextual_relevancy_score_{safe_model_name}"
    
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
    
    print(f"Found {len(test_cases)} test cases that need contextual relevancy evaluation")
    if test_cases:
        print(f"Sample document structure: {json.dumps(test_cases[0], indent=2, cls=MongoJSONEncoder)}")
    
    return test_cases

# No custom model needed - DeepEval will use the model set with `deepeval set-ollama` command

# Evaluate contextual relevancy using deepeval
def evaluate_contextual_relevancy(test_case, model):
    # Create a deepeval LLMTestCase with retrieval context
    # Format context properly (could be a list or string)
    if isinstance(test_case["context"], list):
        retrieval_context = test_case["context"]
    else:
        retrieval_context = [test_case["context"]]
        
    llm_test_case = LLMTestCase(
        input=test_case["input"],
        actual_output=test_case["llm_answer"],
        retrieval_context=retrieval_context
    )
    
    # Create the contextual relevancy metric - DeepEval will use the model set with `deepeval set-ollama` command
    metric = ContextualRelevancyMetric(threshold=0.5)
    
    try:
        # Measure contextual relevancy
        metric.measure(llm_test_case)
        return metric.score, metric.reason
    except Exception as e:
        print(f"Error evaluating contextual relevancy: {e}")
        return 0.5, f"Error evaluating: {str(e)}"

# Save results back to MongoDB
def save_results(test_id, contextual_relevancy_score, contextual_relevancy_reason, model):
    client = MongoClient('mongodb://localhost:27018/')
    db = client['rag_evaluation']
    collection = db['contextual_relevancy_tests']
    
    # Convert model name to MongoDB-friendly format
    safe_model_name = model.replace(':', '_').replace('.', '_')
    score_field = f"contextual_relevancy_score_{safe_model_name}"
    reason_field = f"contextual_relevancy_reason_{safe_model_name}"
    
    # Update the document with the evaluation results
    collection.update_one(
        {"_id": test_id},
        {"$set": {
            score_field: contextual_relevancy_score,
            reason_field: contextual_relevancy_reason
        }}
    )

# Main function
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Evaluate contextual relevancy for LLM answers')
    parser.add_argument('--model', type=str, default=DEFAULT_MODEL, 
                        help=f'Model to evaluate (default: {DEFAULT_MODEL})')
    args = parser.parse_args()
    
    print(f"Evaluating contextual relevancy for model: {args.model}")
    
    # Get test cases from MongoDB that need evaluation
    test_cases = get_test_cases(args.model)
    
    # Limit to first 5 test cases
    test_cases = test_cases[:20]
    print(f"Limited to first 5 test cases for testing")
    
    # Process each test case
    for i, test in enumerate(test_cases, 1):
        print(f"\nEvaluating Test Case {i}/{len(test_cases)}: {test['input']}")
        
        # Evaluate contextual relevancy using deepeval
        contextual_relevancy_score, contextual_relevancy_reason = evaluate_contextual_relevancy(test, test['model'])
        
        # Print results
        print(f"Answer: {test['llm_answer']}")
        print(f"Contextual Relevancy Score: {contextual_relevancy_score}")
        print(f"Contextual Relevancy Reason: {contextual_relevancy_reason}")
        
        # Save results back to MongoDB
        save_results(test["_id"], contextual_relevancy_score, contextual_relevancy_reason, test['model'])
        print(f"✓ Results saved to database")
    
    print("\nContextual relevancy evaluation completed for all test cases.")
