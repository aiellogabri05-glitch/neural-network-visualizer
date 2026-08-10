import json
from pathlib import Path


EXPECTED_SHAPES = {
    "W1": (64, 64),
    "b1": (64,),
    "W2": (64, 64),
    "b2": (64,),
    "W3": (64, 10),
    "b3": (10,),
}


def shape_of(value):
    if not isinstance(value, list):
        return ()
    if not value:
        return (0,)
    if isinstance(value[0], list):
        if not all(isinstance(row, list) for row in value):
            return (len(value), "mixed")
        row_lengths = {len(row) for row in value}
        if len(row_lengths) != 1:
            return (len(value), "ragged")
        return (len(value), row_lengths.pop())
    return (len(value),)


def main():
    weights_path = Path("weights.json")
    data = json.loads(weights_path.read_text(encoding="utf-8"))

    errors = []
    for name, expected_shape in EXPECTED_SHAPES.items():
        if name not in data:
            errors.append(f"- missing key: {name}")
            continue

        actual_shape = shape_of(data[name])
        if actual_shape != expected_shape:
            errors.append(f"- {name}: expected {expected_shape}, got {actual_shape}")

    if errors:
        print("weights.json validation failed:")
        print("\n".join(errors))
        raise SystemExit(1)

    print("weights.json OK: 64 -> 64 -> 64 -> 10")


if __name__ == "__main__":
    main()
