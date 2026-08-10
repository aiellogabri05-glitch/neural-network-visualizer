console.log("app.js caricato");

let networkWeights = null;

fetch('weights.json')
  .then(response => response.json())
  .then(weights => {
    networkWeights = weights;
    console.log("Pesi caricati, pronto a fare previsioni");
  })
  .catch(err => console.error("Errore nel caricare i pesi:", err));

  const GRID_SIZE = 8;
const grid = document.getElementById('grid');
const pixelValues = new Array(64).fill(0);  // qui teniamo i 64 valori (0-16)

// Creiamo dinamicamente i 64 div
for (let i = 0; i < 64; i++) {
  const pixel = document.createElement('div');
  pixel.className = 'pixel';
  pixel.dataset.index = i;  // memorizza a quale posizione (0-63) corrisponde
  grid.appendChild(pixel);
}

console.log("Griglia creata, numero di pixel:", grid.children.length);

let isDrawing = false;

document.addEventListener('mousedown', () => { isDrawing = true; });
document.addEventListener('mouseup', () => { isDrawing = false; });

function setPixelValue(index, newValue) {
  // newValue tra 0 e 16
  const clamped = Math.max(0, Math.min(16, newValue));
  pixelValues[index] = clamped;

  const pixelEl = grid.children[index];
  const gray = 255 - Math.round((clamped / 16) * 255); // 16 -> 0 (nero), 0 -> 255 (bianco)
  pixelEl.style.backgroundColor = `rgb(${gray}, ${gray}, ${gray})`;
}

function darkenPixel(index) {
  setPixelValue(index, pixelValues[index] + 6);

  if (networkWeights) {
    const result = forwardPass(networkWeights);
    updateNetworkVisual(result);  // <-- nuovo

    let bestDigit = 0;
    for (let i = 1; i < result.probabilities.length; i++) {
      if (result.probabilities[i] > result.probabilities[bestDigit]) bestDigit = i;
    }
    const confidence = (result.probabilities[bestDigit] * 100).toFixed(1);
    document.getElementById('prediction').textContent = `Predizione: ${bestDigit} (${confidence}%)`;
  }
}

// Ricolleghiamoci a ogni pixel creato prima
for (let i = 0; i < 64; i++) {
  const pixelEl = grid.children[i];
  pixelEl.addEventListener('mouseover', () => {
    if (isDrawing) darkenPixel(i);
  });
  pixelEl.addEventListener('mousedown', () => {
    darkenPixel(i); // così funziona anche solo cliccando, senza trascinare
  });
}

function neuronOutput(inputs, weights, bias) {
  let sum = bias;
  for (let i = 0; i < inputs.length; i++) {
    sum += inputs[i] * weights[i];
  }
  return sum;
}

function relu(x) {
  return Math.max(0, x);
}

function computeLayer(inputs, weightsMatrix, biases) {
  const numNeurons = biases.length; // quanti neuroni ha questo strato
  const outputs = new Array(numNeurons).fill(0);

  // Per ogni neurone di destinazione...
  for (let neuron = 0; neuron < numNeurons; neuron++) {
    let sum = biases[neuron];
    // ...sommo il contributo di ogni input
    for (let i = 0; i < inputs.length; i++) {
      sum += inputs[i] * weightsMatrix[i][neuron];
    }
    outputs[neuron] = sum;
  }
  return outputs;
}

function forwardPass(weights) {
  // Input: i 64 valori di pixelValues, normalizzati 0-16 -> 0-1 (come nel training!)
  const input = pixelValues.map(v => v / 16);

  // Strato 1
  const z1 = computeLayer(input, weights.W1, weights.b1);
  const h1 = z1.map(relu);

  // Strato 2
  const z2 = computeLayer(h1, weights.W2, weights.b2);
  const h2 = z2.map(relu);

  // Strato output + softmax per trasformarlo in probabilità
  const z3 = computeLayer(h2, weights.W3, weights.b3);
  const probabilities = softmax(z3);

  return { input, h1, h2, probabilities };
}

function softmax(values) {
  // Trucco per stabilità numerica: sottraiamo il massimo prima di elevare a potenza
  // (altrimenti con numeri grandi si rischia un overflow — dettaglio tecnico, fidati e basta)
  const maxVal = Math.max(...values);
  const exps = values.map(v => Math.exp(v - maxVal));
  const sumExps = exps.reduce((a, b) => a + b, 0);
  return exps.map(e => e / sumExps);
}

const svg = document.getElementById('network');
const SVG_NS = "http://www.w3.org/2000/svg";

const linesGroup = document.createElementNS(SVG_NS, "g");
svg.insertBefore(linesGroup, svg.firstChild);

// Calcola le posizioni Y di N neuroni distribuiti in una colonna, dentro un'altezza data
function layerPositions(count, height, topMargin = 20) {
  const usableHeight = height - topMargin * 2;
  const step = count > 1 ? usableHeight / (count - 1) : 0;
  const positions = [];
  for (let i = 0; i < count; i++) {
    positions.push(topMargin + i * step);
  }
  return positions;
}

const H1_X = 150, H2_X = 300, OUT_X = 450;
const h1Y = layerPositions(64, 400);
const h2Y = layerPositions(64, 400);
const outY = layerPositions(10, 400, 40); // margine più grande, sono solo 10

console.log("Posizioni H1:", h1Y);

function createCircle(cx, cy, r, fill) {
  const circle = document.createElementNS(SVG_NS, "circle");
  circle.setAttribute("cx", cx);
  circle.setAttribute("cy", cy);
  circle.setAttribute("r", r);
  circle.setAttribute("fill", fill);
  svg.appendChild(circle);
  return circle; // lo restituiamo per poterlo ricolorare dopo
}

const h1Circles = h1Y.map(y => createCircle(H1_X, y, 3, "#333"));
const h2Circles = h2Y.map(y => createCircle(H2_X, y, 3, "#333"));
const outCircles = outY.map(y => createCircle(OUT_X, y, 12, "#333"));

console.log("Cerchi creati:", h1Circles.length, h2Circles.length, outCircles.length);

function activationColor(value, maxValue) {
  const t = maxValue > 0 ? Math.min(1, value / maxValue) : 0;
  const r = 255, g = Math.round(180 - t * 80), b = Math.round(84 - t * 84);
  const alpha = 0.15 + t * 0.85;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function updateNetworkVisual(result) {
  const maxH1 = Math.max(...result.h1, 0.001);
  const maxH2 = Math.max(...result.h2, 0.001);

  h1Circles.forEach((circle, i) => {
    circle.setAttribute("fill", activationColor(result.h1[i], maxH1));
  });
  h2Circles.forEach((circle, i) => {
    circle.setAttribute("fill", activationColor(result.h2[i], maxH2));
  });
  outCircles.forEach((circle, i) => {
    circle.setAttribute("fill", activationColor(result.probabilities[i], 1));
  });
}

// Trova le K connessioni con contributo più forte tra un layer sorgente e uno di destinazione
function topConnections(sourceValues, weightMatrix, k) {
  const connections = [];
  for (let i = 0; i < sourceValues.length; i++) {
    const sourceVal = sourceValues[i];
    if (sourceVal === 0) continue; // neurone spento, nessun contributo
    const weightsRow = weightMatrix[i];
    for (let j = 0; j < weightsRow.length; j++) {
      const contribution = sourceVal * weightsRow[j];
      connections.push({ from: i, to: j, strength: contribution });
    }
  }
  // Ordina per forza assoluta (positiva o negativa, entrambe interessanti) e prendi le prime K
  connections.sort((a, b) => Math.abs(b.strength) - Math.abs(a.strength));
  return connections.slice(0, k);
}

console.log("Funzione topConnections pronta");

function createLine(x1, y1, x2, y2, color, width) {
  const line = document.createElementNS(SVG_NS, "line");
  line.setAttribute("x1", x1);
  line.setAttribute("y1", y1);
  line.setAttribute("x2", x2);
  line.setAttribute("y2", y2);
  line.setAttribute("stroke", color);
  line.setAttribute("stroke-width", width);
  linesGroup.appendChild(line);
}

function drawConnections(result) {
  linesGroup.innerHTML = ""; // cancella le linee del disegno precedente prima di ridisegnare

  const h1h2 = topConnections(result.h1, networkWeights.W2, 60);
  const h2out = topConnections(result.h2, networkWeights.W3, 40);

  const maxH1H2 = Math.max(...h1h2.map(c => Math.abs(c.strength)), 0.001);
  const maxH2Out = Math.max(...h2out.map(c => Math.abs(c.strength)), 0.001);

  h1h2.forEach(c => {
    const t = Math.abs(c.strength) / maxH1H2;
    // arancione = contributo positivo (eccita), blu = negativo (inibisce)
    const color = c.strength >= 0
      ? `rgba(255,180,84,${0.15 + t * 0.6})`
      : `rgba(110,130,200,${0.15 + t * 0.6})`;
    createLine(H1_X, h1Y[c.from], H2_X, h2Y[c.to], color, 1 + t * 2);
  });

  h2out.forEach(c => {
    const t = Math.abs(c.strength) / maxH2Out;
    const color = c.strength >= 0
      ? `rgba(255,180,84,${0.15 + t * 0.6})`
      : `rgba(110,130,200,${0.15 + t * 0.6})`;
    createLine(H2_X, h2Y[c.from], OUT_X, outY[c.to], color, 1 + t * 2);
  });
}

function darkenPixel(index) {
  setPixelValue(index, pixelValues[index] + 6);

  if (networkWeights) {
    const result = forwardPass(networkWeights);
    updateNetworkVisual(result);
    drawConnections(result);  // <-- nuovo

    let bestDigit = 0;
    for (let i = 1; i < result.probabilities.length; i++) {
      if (result.probabilities[i] > result.probabilities[bestDigit]) bestDigit = i;
    }
    const confidence = (result.probabilities[bestDigit] * 100).toFixed(1);
    document.getElementById('prediction').textContent = `Predizione: ${bestDigit} (${confidence}%)`;
  }
}

outY.forEach((y, digit) => {
  const label = document.createElementNS(SVG_NS, "text");
  label.setAttribute("x", OUT_X + 22);
  label.setAttribute("y", y + 5); // +5 per centrare verticalmente rispetto al pallino
  label.setAttribute("fill", "#ccc");
  label.setAttribute("font-family", "monospace");
  label.setAttribute("font-size", "14");
  label.textContent = digit;
  svg.appendChild(label);
});

document.getElementById('clearBtn').addEventListener('click', () => {
  for (let i = 0; i < 64; i++) {
    setPixelValue(i, 0);
  }
  linesGroup.innerHTML = "";
  h1Circles.forEach(c => c.setAttribute("fill", "#333"));
  h2Circles.forEach(c => c.setAttribute("fill", "#333"));
  outCircles.forEach(c => c.setAttribute("fill", "#333"));
  document.getElementById('prediction').textContent = "Predizione: -";
});