import requests

def get_embedding(text, model="nomic-embed-text"):
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={"model": model, "prompt": text}
    )
    return response.json()["embedding"]


if __name__ == "__main__":
    vettore = get_embedding("il mio modello ha 64 neuroni")
    print("Lunghezza del vettore:", len(vettore))
    print("Primi 5 numeri:", vettore[:5])

    domanda = get_embedding("quanti neuroni ha la rete?")
    frase_diversa = get_embedding("mi piace il gelato al pistacchio")

    def similarita(v1, v2):
        # "coseno di similarità": più è vicino a 1, più le frasi si assomigliano nel significato
        prodotto = sum(a * b for a, b in zip(v1, v2))
        lunghezza1 = sum(a * a for a in v1) ** 0.5
        lunghezza2 = sum(b * b for b in v2) ** 0.5
        return prodotto / (lunghezza1 * lunghezza2)

    print()
    print("Similarita' tra 'modello 64 neuroni' e 'quanti neuroni ha la rete?':", similarita(vettore, domanda))
    print("Similarita' tra 'modello 64 neuroni' e 'mi piace il gelato':", similarita(vettore, frase_diversa))  