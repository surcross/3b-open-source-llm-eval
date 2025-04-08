from pydantic import BaseModel

class ExampleSchema(BaseModel):
    name: str


from deepeval import evaluate
from deepeval.metrics import JsonCorrectnessMetric
from deepeval.test_case import LLMTestCase


metric = JsonCorrectnessMetric(
    expected_schema=ExampleSchema,
    include_reason=True
)
test_case = LLMTestCase(
    input="Output me a random Json with the 'name' key",
    # Replace this with the actual output from your LLM application
    actual_output='{"name": "Jessica", "age": 32, "city": "Chicago", "hobbies": ["reading", "cooking", "yoga"]}'
)

metric.measure(test_case)
print(metric.score)
print(metric.reason)

# or evaluate test cases in bulk
evaluate([test_case], [metric])