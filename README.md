# Neural Network Visualizer

[![LIVE DEMO](https://img.shields.io/badge/LIVE-DEMO-brightgreen)](https://aiellogabri05-glitch.github.io/neural-network-visualizer/)

A compact neural network visualizer for handwritten digit recognition. The current model is a `64 -> 64 -> 64 -> 10` multilayer perceptron trained on 8x8 digit images, with the forward pass rendered live in the browser as an interactive 3D scene.


![Neural Network Visualizer demo](demo.gif)

## How It Works

Draw a digit on the 8x8 input layer and watch the network update in real time:

- The input layer contains 64 drawable pixels.
- Two hidden layers contain 64 neurons each.
- Connections are colored by current contribution: positive values excite, negative values inhibit.
- The output layer shows probabilities for digits `0` through `9`.

## Architecture

- **Training**: Python trains a scikit-learn `MLPClassifier` on the `digits` dataset.
- **Export**: `train.py` writes learned weights and biases to `weights.json`.
- **Inference**: `app.js` reimplements the forward pass in vanilla JavaScript: matrix multiplication, ReLU, and softmax.
- **Visualization**: Three.js renders the input layer, hidden layers, output layer, and connection strengths in 3D.

## Run Locally

Because the app loads `weights.json` and uses JavaScript modules, serve the folder with a local web server:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

## Python Setup

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Retrain The Model

```bash
python train.py
```

This regenerates `weights.json`.

## Validate The Export

```bash
python validate_weights.py
```

## Run The Local Agent

Start the first text-only Jarvis shell:

```bash
python -m agent.agent_loop
```

Try commands such as:

```text
help
health
ask how does the agent memory work?
files
inspect agent/agent_loop.py
read README.md
search forwardPass
remember the visualizer uses a 64 -> 64 -> 64 -> 10 model
recall visualizer
todo add add voice input later
todo list
validate
diff
explain
roadmap
```

Guarded commands ask for confirmation in interactive mode:

```text
train
commit <message>
push
```

## Toward Jarvis

This project is a strong visual foundation, but an agent needs more than a classifier. See `JARVIS_ROADMAP.md` for the next architecture layers: agent loop, tools, memory, voice, permissions, and automation.
