from sklearn.datasets import load_digits
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split

digits = load_digits()
X = digits.data / 16.0
y = digits.target

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.15, random_state=42, stratify=y
)

# Definiamo diverse architetture da confrontare
architectures = {
    "Originale (16,16)":        {"hidden_layer_sizes": (16, 16), "alpha": 0.0001},
    "Più larga (64,64)":        {"hidden_layer_sizes": (64, 64), "alpha": 0.0001},
    "Più profonda (32,32,32)":  {"hidden_layer_sizes": (32, 32, 32), "alpha": 0.0001},
    "Larga + regolarizzata":    {"hidden_layer_sizes": (64, 64), "alpha": 0.01},
}

print(f"{'Architettura':<25} {'Train Acc':>10} {'Test Acc':>10} {'Gap':>8}")
print("-" * 55)

for name, params in architectures.items():
    clf = MLPClassifier(
        activation='relu',
        max_iter=3000,
        random_state=42,
        **params
    )
    clf.fit(X_train, y_train)
    train_acc = clf.score(X_train, y_train)
    test_acc = clf.score(X_test, y_test)
    gap = train_acc - test_acc  # più è grande, più overfitta
    print(f"{name:<25} {train_acc:>10.1%} {test_acc:>10.1%} {gap:>8.1%}")