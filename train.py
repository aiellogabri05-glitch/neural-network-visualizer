from sklearn.datasets import load_digits
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split

# 1. Carica i dati
digits = load_digits()
X = digits.data / 16.0   # normalizziamo: da 0-16 a 0-1 (le reti imparano meglio con numeri piccoli)
y = digits.target        # le etichette: 0,1,2...9

# 2. Dividiamo in dati di training (per imparare) e di test (per verificare che non abbia solo memorizzato)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.15, random_state=42, stratify=y
)
print("Immagini per allenare:", len(X_train))
print("Immagini per testare:", len(X_test))

# 3. Creiamo la rete: 2 strati nascosti da 64 neuroni ciascuno
clf = MLPClassifier(
    hidden_layer_sizes=(64, 64),
    activation='relu',
    max_iter=3000,
    random_state=42
)

# 4. Alleniamo (qui avviene tutta la magia di backpropagation, ripetuta migliaia di volte)
clf.fit(X_train, y_train)

# 5. Verifichiamo quanto ha imparato bene
train_acc = clf.score(X_train, y_train)
test_acc = clf.score(X_test, y_test)
print(f"Accuratezza sui dati visti in training: {train_acc:.1%}")
print(f"Accuratezza su dati MAI visti (test): {test_acc:.1%}")

print()
print("Forma coefs_[0] (Input->Hidden1):", clf.coefs_[0].shape)
print("Forma coefs_[1] (Hidden1->Hidden2):", clf.coefs_[1].shape)
print("Forma coefs_[2] (Hidden2->Output):", clf.coefs_[2].shape)
print("Forma intercepts_[0]:", clf.intercepts_[0].shape)
print("Forma intercepts_[1]:", clf.intercepts_[1].shape)
print("Forma intercepts_[2]:", clf.intercepts_[2].shape)

import json

pesi = {
    "W1": clf.coefs_[0].tolist(),      # Input -> Hidden1 (64x64)
    "b1": clf.intercepts_[0].tolist(), # bias Hidden1 (64)
    "W2": clf.coefs_[1].tolist(),      # Hidden1 -> Hidden2 (64x64)
    "b2": clf.intercepts_[1].tolist(), # bias Hidden2 (64)
    "W3": clf.coefs_[2].tolist(),      # Hidden2 -> Output (64x10)
    "b3": clf.intercepts_[2].tolist(), # bias Output (10)
}

with open("weights.json", "w") as f:
    json.dump(pesi, f)

print()
print("Pesi salvati in weights.json")
