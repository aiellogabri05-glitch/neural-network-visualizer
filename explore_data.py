from sklearn.datasets import load_digits
import matplotlib.pyplot as plt

# Carica il dataset: migliaia di cifre scritte a mano, 8x8 pixel ciascuna
digits = load_digits()

print("Numero totale di immagini:", len(digits.data))
print("Forma di un'immagine (grezza):", digits.images[0].shape)
print("Forma 'appiattita' (flatten):", digits.data[0].shape)
print("Etichetta della prima immagine:", digits.target[0])
print()
print("I valori dei pixel (0=bianco, 16=nero pieno):")
print(digits.images[0].astype(int))

# Mostriamo l'immagine per davvero
plt.imshow(digits.images[0], cmap='gray')
plt.title(f"Questa è la cifra: {digits.target[0]}")
plt.show()