import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

console.log("Three.js caricato:", THREE.REVISION);

// ---------- Pesi della rete ----------
let networkWeights = null;

fetch('weights.json')
  .then(response => response.json())
  .then(weights => {
    networkWeights = weights;
    console.log("Pesi caricati, pronto a fare previsioni");
    console.log("Neuroni per layer:", weights.W1.length, weights.W1[0].length, weights.W3[0].length);
  })
  .catch(err => console.error("Errore nel caricare i pesi:", err));

// ---------- Matematica della rete (invariata) ----------
function relu(x) {
  return Math.max(0, x);
}

function computeLayer(inputs, weightsMatrix, biases) {
  const numNeurons = biases.length;
  const outputs = new Array(numNeurons).fill(0);
  for (let neuron = 0; neuron < numNeurons; neuron++) {
    let sum = biases[neuron];
    for (let i = 0; i < inputs.length; i++) {
      sum += inputs[i] * weightsMatrix[i][neuron];
    }
    outputs[neuron] = sum;
  }
  return outputs;
}

function softmax(values) {
  const maxVal = Math.max(...values);
  const exps = values.map(v => Math.exp(v - maxVal));
  const sumExps = exps.reduce((a, b) => a + b, 0);
  return exps.map(e => e / sumExps);
}

function forwardPass(weights, pixelValues) {
  const input = pixelValues.map(v => v / 16);
  const z1 = computeLayer(input, weights.W1, weights.b1);
  const h1 = z1.map(relu);
  const z2 = computeLayer(h1, weights.W2, weights.b2);
  const h2 = z2.map(relu);
  const z3 = computeLayer(h2, weights.W3, weights.b3);
  const probabilities = softmax(z3);
  return { input, h1, h2, probabilities };
}

function topConnections(sourceValues, weightMatrix, k) {
  const connections = [];
  for (let i = 0; i < sourceValues.length; i++) {
    const sourceVal = sourceValues[i];
    if (sourceVal === 0) continue;
    const weightsRow = weightMatrix[i];
    for (let j = 0; j < weightsRow.length; j++) {
      connections.push({ from: i, to: j, strength: sourceVal * weightsRow[j] });
    }
  }
  connections.sort((a, b) => Math.abs(b.strength) - Math.abs(a.strength));
  return connections.slice(0, k);
}

// ---------- Setup scena 3D ----------
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0a0a);

const camera = new THREE.PerspectiveCamera(
  50,
  window.innerWidth / window.innerHeight,
  0.1,
  1000
);
camera.position.set(15, 10, 70);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0, 0);
controls.enableDamping = true;
controls.update();

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// ---------- Layout dei layer nello spazio ----------
const LAYER_Z = { input: 24, hidden1: 8, hidden2: -8, output: -24 };

function gridLayout(count, spacing) {
  const cols = Math.ceil(Math.sqrt(count));
  const rows = Math.ceil(count / cols);
  const positions = [];
  for (let i = 0; i < count; i++) {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const x = (col - (cols - 1) / 2) * spacing;
    const y = ((rows - 1) / 2 - row) * spacing;
    positions.push({ x, y });
  }
  return positions;
}

const hidden1Layout = gridLayout(64, 3.2);
const hidden2Layout = gridLayout(64, 3.2);
const outputLayout = gridLayout(10, 4);
const inputLayout = gridLayout(64, 2.8);

console.log("Layout hidden1 (prime 3 posizioni):", hidden1Layout.slice(0, 3));

// ---------- Colori per layer ----------
const LAYER_COLORS = {
  input:   new THREE.Color(1.0, 0.55, 0.15),
  hidden1: new THREE.Color(0.15, 0.75, 0.95),
  hidden2: new THREE.Color(0.65, 0.35, 0.95),
  output:  new THREE.Color(1.0, 0.82, 0.25),
};
const DIM_COLOR = new THREE.Color(0.08, 0.08, 0.1);

function activationColor(value, maxValue, layerColor) {
  const t = maxValue > 0 ? Math.min(1, value / maxValue) : 0;
  const boosted = Math.pow(t, 0.6);
  return DIM_COLOR.clone().lerp(layerColor, boosted);
}

// ---------- Sfere dei neuroni ----------
const sphereGeometry = new THREE.SphereGeometry(0.6, 12, 12);

function createNeuronLayer(layout, z, color) {
  const material = new THREE.MeshBasicMaterial({ color });
  const mesh = new THREE.InstancedMesh(sphereGeometry, material, layout.length);

  const dummy = new THREE.Object3D();
  layout.forEach((pos, i) => {
    dummy.position.set(pos.x, pos.y, z);
    dummy.updateMatrix();
    mesh.setMatrixAt(i, dummy.matrix);
  });
  mesh.instanceMatrix.needsUpdate = true;

  scene.add(mesh);
  return mesh;
}

const hidden1Mesh = createNeuronLayer(hidden1Layout, LAYER_Z.hidden1, 0xffffff);
const hidden2Mesh = createNeuronLayer(hidden2Layout, LAYER_Z.hidden2, 0xffffff);
const outputMesh = createNeuronLayer(outputLayout, LAYER_Z.output, 0xffffff);

scene.add(new THREE.AmbientLight(0xffffff, 0.6));
const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
dirLight.position.set(10, 10, 20);
scene.add(dirLight);

console.log("Neuroni creati:", hidden1Mesh.count, hidden2Mesh.count, outputMesh.count);

// ---------- Layer di input disegnabile ----------
const pixelValues = new Array(64).fill(0);
window.pixelValues = pixelValues; // solo per debug dalla console

const pixelGeometry = new THREE.PlaneGeometry(2.5, 2.5);
const inputMesh = new THREE.InstancedMesh(
  pixelGeometry,
  new THREE.MeshBasicMaterial({ color: 0x1a1a1a, side: THREE.DoubleSide }),
  64
);

const dummyInput = new THREE.Object3D();
inputLayout.forEach((pos, i) => {
  dummyInput.position.set(pos.x, pos.y, LAYER_Z.input);
  dummyInput.updateMatrix();
  inputMesh.setMatrixAt(i, dummyInput.matrix);
});
inputMesh.instanceMatrix.needsUpdate = true;
scene.add(inputMesh);

function updatePixelColor(index) {
  const t = pixelValues[index] / 16;
  const c = DIM_COLOR.clone().lerp(LAYER_COLORS.input, Math.pow(t, 0.6));
  inputMesh.setColorAt(index, c);
  inputMesh.instanceColor.needsUpdate = true;
}

// ---------- Raycasting: dal mouse al pixel 3D ----------
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
let isDrawing = false;

function paintAtMouse(event) {
  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObject(inputMesh);

  if (hits.length > 0) {
    const index = hits[0].instanceId;
    pixelValues[index] = Math.min(16, pixelValues[index] + 6);
    updatePixelColor(index);
    updateNetworkVisual();
  }
}

renderer.domElement.addEventListener('pointerdown', (e) => {
  if (e.button !== 0) return;

  mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObject(inputMesh);

  if (hits.length > 0) {
    isDrawing = true;
    controls.enabled = false;
    paintAtMouse(e);
  }
});
renderer.domElement.addEventListener('pointermove', (e) => {
  if (isDrawing) paintAtMouse(e);
});
window.addEventListener('pointerup', () => {
  isDrawing = false;
  controls.enabled = true;
});

console.log("Layer di input pronto:", inputMesh.count);

// ---------- Connessioni 3D ----------
function buildConnectionGeometry(sourceLayout, sourceZ, targetLayout, targetZ) {
  const segments = sourceLayout.length * targetLayout.length;
  const positions = new Float32Array(segments * 2 * 3);
  const colors = new Float32Array(segments * 2 * 3);

  let p = 0;
  for (let i = 0; i < sourceLayout.length; i++) {
    const s = sourceLayout[i];
    for (let j = 0; j < targetLayout.length; j++) {
      const t = targetLayout[j];
      positions[p]   = s.x; positions[p+1] = s.y; positions[p+2] = sourceZ;
      positions[p+3] = t.x; positions[p+4] = t.y; positions[p+5] = targetZ;
      p += 6;
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  return geometry;
}

function createConnectionLines(sourceLayout, sourceZ, targetLayout, targetZ) {
  const geometry = buildConnectionGeometry(sourceLayout, sourceZ, targetLayout, targetZ);
  const material = new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.35 });
  const lines = new THREE.LineSegments(geometry, material);
  scene.add(lines);
  return lines;
}

const inputHidden1Lines = createConnectionLines(inputLayout, LAYER_Z.input, hidden1Layout, LAYER_Z.hidden1);
const hidden1Hidden2Lines = createConnectionLines(hidden1Layout, LAYER_Z.hidden1, hidden2Layout, LAYER_Z.hidden2);
const hidden2OutputLines = createConnectionLines(hidden2Layout, LAYER_Z.hidden2, outputLayout, LAYER_Z.output);

console.log("Connessioni create:", inputHidden1Lines.geometry.attributes.position.count / 2,
                                    hidden1Hidden2Lines.geometry.attributes.position.count / 2,
                                    hidden2OutputLines.geometry.attributes.position.count / 2);

const EXCITE_COLOR = new THREE.Color(1.0, 0.55, 0.15);
const INHIBIT_COLOR = new THREE.Color(0.35, 0.45, 0.95);
const CONN_DARK = new THREE.Color(0.03, 0.03, 0.04);

function updateConnectionColors(linesObj, sourceValues, weightMatrix) {
  const colorAttr = linesObj.geometry.attributes.color;
  const arr = colorAttr.array;

  const numTargets = weightMatrix[0].length;
  const contributions = new Float32Array(sourceValues.length * numTargets);
  let maxAbs = 0.001;
  let idx = 0;
  for (let i = 0; i < sourceValues.length; i++) {
    const sv = sourceValues[i];
    const row = weightMatrix[i];
    for (let j = 0; j < numTargets; j++) {
      const c = sv * row[j];
      contributions[idx++] = c;
      if (Math.abs(c) > maxAbs) maxAbs = Math.abs(c);
    }
  }

  idx = 0;
  let p = 0;
  for (let i = 0; i < sourceValues.length; i++) {
    for (let j = 0; j < numTargets; j++) {
      const t = Math.min(1, Math.abs(contributions[idx]) / maxAbs);
      const boosted = Math.pow(t, 0.5);
      const base = contributions[idx] >= 0 ? EXCITE_COLOR : INHIBIT_COLOR;
      const c = CONN_DARK.clone().lerp(base, boosted);
      arr[p] = c.r; arr[p+1] = c.g; arr[p+2] = c.b;
      arr[p+3] = c.r; arr[p+4] = c.g; arr[p+5] = c.b;
      idx++; p += 6;
    }
  }
  colorAttr.needsUpdate = true;
}

// ---------- Aggiornare i colori dei neuroni in base all'attivazione ----------
function updateLayerColors(mesh, values, maxValue, layerColor) {
  for (let i = 0; i < values.length; i++) {
    mesh.setColorAt(i, activationColor(values[i], maxValue, layerColor));
  }
  mesh.instanceColor.needsUpdate = true;
}

function updateNetworkVisual() {
  if (!networkWeights) return;

  const result = forwardPass(networkWeights, pixelValues);

  updateConnectionColors(inputHidden1Lines, result.input, networkWeights.W1);
  updateConnectionColors(hidden1Hidden2Lines, result.h1, networkWeights.W2);
  updateConnectionColors(hidden2OutputLines, result.h2, networkWeights.W3);

  const maxH1 = Math.max(...result.h1, 0.001);
  const maxH2 = Math.max(...result.h2, 0.001);

  updateLayerColors(hidden1Mesh, result.h1, maxH1, LAYER_COLORS.hidden1);
  updateLayerColors(hidden2Mesh, result.h2, maxH2, LAYER_COLORS.hidden2);
  updateLayerColors(outputMesh, result.probabilities, 1, LAYER_COLORS.output);

  let bestDigit = 0;
  for (let i = 1; i < result.probabilities.length; i++) {
    if (result.probabilities[i] > result.probabilities[bestDigit]) bestDigit = i;
  }
  const confidence = (result.probabilities[bestDigit] * 100).toFixed(1);
  document.getElementById('prediction').textContent = `Predizione: ${bestDigit} (${confidence}%)`;

  return result;
}

// ---------- Loop di animazione ----------
function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
animate();

console.log("Scena 3D inizializzata");

document.getElementById('clearBtn').addEventListener('click', () => {
  for (let i = 0; i < 64; i++) {
    pixelValues[i] = 0;
    updatePixelColor(i);
  }
  updateNetworkVisual();
});