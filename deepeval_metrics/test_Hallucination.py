from pymongo import MongoClient
from deepeval.metrics.hallucination.hallucination import HallucinationMetric
from deepeval.test_case import LLMTestCase
import os

# Function to get test cases from MongoDB
def get_test_cases():
    client = MongoClient('mongodb://localhost:27018/')
    db = client['rag_evaluation']
    collection = db['hallucination_tests']
    
    # Retrieve test cases with context and answers
    test_cases = list(collection.find({}))
    print(f"Found {len(test_cases)} test cases in the database")
    
    # Print a sample document structure
    if test_cases:
        print(f"Sample document structure: {test_cases[0]}")
    
    return test_cases


# Evaluate hallucination using deepeval with Ollama model
def evaluate_hallucination(test_case):
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
def save_results(test_id, hallucination_score, hallucination_reason):
    client = MongoClient('mongodb://localhost:27018/')
    db = client['rag_evaluation']
    collection = db['hallucination_tests']
    
    # Update the document with the evaluation results
    collection.update_one(
        {"_id": test_id},
        {"$set": {
            "hallucination_score": hallucination_score,
            "hallucination_reason": hallucination_reason
        }}
    )

# Main function
if __name__ == "__main__":
    # First, make sure you've set your Ollama model with the CLI command:
    # deepeval set-ollama gemma3:4b
    # If you haven't done this yet, you'll need to run it in your terminal first
    
    # Get test cases from MongoDB
    test_cases = get_test_cases()
    
    # Process each test case  看多了就眼熟了. 
    for i, test in enumerate(test_cases, 1):
        # Skip test cases without answers
        if not test.get("llm_answer"):
            print(f"\nSkipping Test Case {i} (no answer available): {test['input']}")
            continue
            
        # Skip test cases that already have evaluation results
        if "hallucination_score" in test and "hallucination_reason" in test:
            print(f"\nSkipping Test Case {i} (already evaluated): {test['input']}")
            continue
        
        # Evaluate hallucination using deepeval    tuple 类型的赋值方式
        hallucination_score, hallucination_reason = evaluate_hallucination(test)
        
        # Print results
        print(f"\nTest Case {i}: {test['input']}")
        print(f"Context: {test['context']}")
        print(f"Answer: {test['llm_answer']}")
        print(f"Hallucination Score: {hallucination_score}")
        print(f"Hallucination Reason: {hallucination_reason}")
        
        # Save results back to MongoDB
        save_results(test["_id"], hallucination_score, hallucination_reason)
