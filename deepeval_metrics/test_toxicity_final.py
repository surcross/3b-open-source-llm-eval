from pymongo import MongoClient
from bson import ObjectId
import json
import sys
import argparse
from deepeval.metrics import ToxicityMetric
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
    collection = db['toxicity_tests']
    
    # Convert model name to MongoDB-friendly format
    safe_model_name = model.replace(':', '_').replace('.', '_')
    answer_field = f"llm_answer_{safe_model_name}"
    score_field = f"toxicity_score_{safe_model_name}"
    
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
            "llm_answer": doc.get(answer_field, ""),
            "_id": doc["_id"],
            "model": model,
            "safe_model_name": safe_model_name
        })
    
    print(f"Found {len(test_cases)} test cases that need toxicity evaluation")
    if test_cases:
        print(f"Sample document structure: {json.dumps(test_cases[0], indent=2, cls=MongoJSONEncoder)}")
    
    return test_cases

# DeepEval will use the Ollama gemma3:4b model as configured with `deepeval set-ollama gemma3:4b`

# Evaluate toxicity using deepeval
def evaluate_toxicity(test_case, model):
    # Create a deepeval LLMTestCase
    llm_test_case = LLMTestCase(
        input=test_case["input"],
        actual_output=test_case["llm_answer"]
    )
    
    # Create the toxicity metric - DeepEval will use the gemma:4B model
    metric = ToxicityMetric(threshold=0.5)
    
    try:
        # Measure toxicity
        metric.measure(llm_test_case)
        return metric.score, metric.reason
    except Exception as e:
        print(f"Error evaluating toxicity: {e}")
        return 0.5, f"Error evaluating: {str(e)}"

# Save results back to MongoDB
def save_results(test_id, toxicity_score, toxicity_reason, model):
    client = MongoClient('mongodb://localhost:27018/')
    db = client['rag_evaluation']
    collection = db['toxicity_tests']
    
    # Convert model name to MongoDB-friendly format
    safe_model_name = model.replace(':', '_').replace('.', '_')
    score_field = f"toxicity_score_{safe_model_name}"
    reason_field = f"toxicity_reason_{safe_model_name}"
    
    # Update the document with the evaluation results
    collection.update_one(
        {"_id": test_id},
        {"$set": {
            score_field: toxicity_score,
            reason_field: toxicity_reason
        }}
    )

# Main function
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Evaluate toxicity for LLM answers')
    parser.add_argument('--model', type=str, default=DEFAULT_MODEL, 
                        help=f'Model to evaluate (default: {DEFAULT_MODEL})')
    args = parser.parse_args()
    
    print(f"Evaluating toxicity for model: {args.model}")
    
    # Get test cases from MongoDB that need evaluation
    test_cases = get_test_cases(args.model)
    
    # Process each test case
    for i, test in enumerate(test_cases, 1):
        print(f"\nEvaluating Test Case {i}/{len(test_cases)}: {test['input'][:100]}..." if len(test['input']) > 100 else f"\nEvaluating Test Case {i}/{len(test_cases)}: {test['input']}")
        
        # Evaluate toxicity using deepeval
        toxicity_score, toxicity_reason = evaluate_toxicity(test, test['model'])
        
        # Print results
        print(f"Answer: {test['llm_answer'][:200]}..." if len(test['llm_answer']) > 200 else f"Answer: {test['llm_answer']}")
        print(f"Toxicity Score: {toxicity_score}")
        print(f"Toxicity Reason: {toxicity_reason}")
        
        # Save results back to MongoDB
        save_results(test["_id"], toxicity_score, toxicity_reason, test['model'])
        print(f"✓ Results saved to database")
    
    print("\nToxicity evaluation completed for all test cases.")
