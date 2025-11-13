import requests
import json

def ask(prompt):
    payload = {
        "model": "gemma:2b",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": True
    }

    response = requests.post(
        "http://localhost:11434/api/chat",
        json=payload,
        stream=True
    )

    final_text = ""

    for line in response.iter_lines():
        if not line:
            continue

        data = json.loads(line.decode("utf-8"))

        # Stream token to terminal
        if "message" in data and "content" in data["message"]:
            token = data["message"]["content"]
            print(token, end="", flush=True)   # LIVE STREAM
            final_text += token

        # Stop when done
        if data.get("done"):
            print()  # newline after streaming
            break

    return final_text


while True:
    request = input("Enter prompt: ")
    ask(request)
