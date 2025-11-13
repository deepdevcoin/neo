from gpt4all import GPT4All
import pathlib
import time
import sys

model_dir = pathlib.Path.home() / ".local" / "share" / "neo" / "models"
model = model_dir / "Phi-3-mini-4k-instruct-q4.gguf"
model_path = str(model)

llm = GPT4All(model_path)
response = llm.generate("Hello")

# Typing effect for initial response
for char in response:
    print(char, end='', flush=True)
    time.sleep(0.03)  # Adjust typing speed here
print()  # Newline after finishing

base_prompt = """
You are an intelligent assistant that answers clearly and concisely.

User: {input}
Assistant:"""

while True:
    request = input("Enter prompt: ")
    prompt = base_prompt.format(input=request)
    response = llm.generate(prompt, max_tokens=150, temp=0.3)
    clean_response = response.replace("<|end|>", "").replace("<|assistant|>", "").strip()
    print(clean_response)
