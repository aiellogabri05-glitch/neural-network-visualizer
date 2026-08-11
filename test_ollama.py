import requests

def ask_ollama(messages, model="llama3.2:3b"):
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False
        }
    )
    data = response.json()
    return data["message"]["content"]


if __name__ == "__main__":
    conversation = []  # qui accumuliamo tutta la cronologia

    print("Chat con Llama locale. Scrivi 'exit' per uscire.\n")
    while True:
        user_input = input("Tu: ")
        if user_input.lower() == "exit":
            break

        conversation.append({"role": "user", "content": user_input})
        reply = ask_ollama(conversation)
        print(f"Llama: {reply}\n")

        conversation.append({"role": "assistant", "content": reply})