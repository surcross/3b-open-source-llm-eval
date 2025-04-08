import ollama

response = ollama.embed(
    model='mistral',  # Use the mistral model
    input='The sky is blue because of rayleigh scattering'
)

response_dict = vars(response)
print(response_dict)