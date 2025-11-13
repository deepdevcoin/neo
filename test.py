from gpt4all import GPT4All
model_path = "/media/karthikeyan/705BA2D832DDA159/neo/models/Phi-3-mini-4k-instruct-q4.gguf"
llm = GPT4All(model_path)
response = llm.generate("Hello")
print(response)
while True:
    request = input("Enter prompt: ")
    print(llm.generate(request))
