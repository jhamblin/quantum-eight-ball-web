const form = document.getElementById("ask-form");
const questionInput = document.getElementById("question");
const qubitButtons = document.querySelectorAll(".qubit-option");
const shakeBtn = document.getElementById("shake-btn");
const ball = document.getElementById("ball");
const status = document.getElementById("status");
const stage = document.getElementById("stage");
const barsEl = document.getElementById("bars");
const stateVector = document.getElementById("state-vector");
const reveal = document.getElementById("reveal");
const revealedText = document.getElementById("revealed-text");
const hitRateEl = document.getElementById("hit-rate");
const circuits = document.getElementById("circuits");
const shakeDiagram = document.getElementById("shake-diagram");
const groverDiagram = document.getElementById("grover-diagram");
const speedup = document.getElementById("speedup");
const classicalBar = document.getElementById("classical-bar");
const quantumBar = document.getElementById("quantum-bar");
const classicalValue = document.getElementById("classical-value");
const quantumValue = document.getElementById("quantum-value");
const speedupCaption = document.getElementById("speedup-caption");
const classicalCurve = document.getElementById("classical-curve");
const quantumCurve = document.getElementById("quantum-curve");
const classicalMarker = document.getElementById("classical-marker");
const quantumMarker = document.getElementById("quantum-marker");

const STEP_PAUSE_MS = 3000;

// Extrapolated well past the 8/16/32 answers this demo actually runs, so
// the sqrt-vs-linear gap is obvious even for the smallest qubit count.
const SPEEDUP_CHART_N_VALUES = [8, 16, 32, 64, 128, 256, 512, 1024, 2048];
const CHART = { left: 60, right: 580, top: 20, bottom: 200 };

// Mirrors optimal_iterations() in app/quantum.py.
function optimalIterations(n) {
  const theta = Math.asin(Math.sqrt(1 / n));
  return Math.round(Math.PI / (4 * theta) - 0.5);
}

let selectedQubits = 3;

qubitButtons.forEach((btn) => {
  btn.classList.toggle("active", Number(btn.dataset.qubits) === selectedQubits);
  btn.addEventListener("click", () => {
    selectedQubits = Number(btn.dataset.qubits);
    qubitButtons.forEach((b) => b.classList.toggle("active", b === btn));
  });
});

function buildBars(n, answers, hiddenIndex) {
  barsEl.innerHTML = "";

  const track = document.createElement("div");
  track.className = "bars-track";
  const labels = document.createElement("div");
  labels.className = "bars-labels";

  for (let i = 0; i < n; i++) {
    const col = document.createElement("div");
    col.className = "bar-col";
    const bar = document.createElement("div");
    bar.className = "bar" + (i === hiddenIndex ? " is-hidden" : "");
    bar.style.height = "2px";
    bar.dataset.answer = answers[i];

    const value = document.createElement("div");
    value.className = "bar-value";
    value.textContent = "0%";
    bar.appendChild(value);

    col.appendChild(bar);
    track.appendChild(col);

    const labelCol = document.createElement("div");
    labelCol.className = "label-col";
    const label = document.createElement("div");
    label.className = "bar-label";
    label.textContent = answers[i];
    label.title = answers[i];
    labelCol.appendChild(label);
    labels.appendChild(labelCol);
  }

  barsEl.appendChild(track);
  barsEl.appendChild(labels);
}

function setBarHeights(probs) {
  const bars = barsEl.querySelectorAll(".bar");
  // Past 8 columns, a percentage on every bar overlaps its neighbors and
  // becomes unreadable -- so only the current frontrunner gets one inline;
  // every bar's exact value is still available via its tooltip.
  const showAllValues = probs.length <= 8;
  const maxIndex = probs.indexOf(Math.max(...probs));

  bars.forEach((bar, i) => {
    const actualPct = probs[i] * 100;
    const heightPct = Math.max(2, actualPct);
    bar.style.height = `${(heightPct / 100) * 220}px`;

    const pctText = `${actualPct.toFixed(1)}%`;
    bar.title = `${bar.dataset.answer} — ${pctText}`;
    bar.querySelector(".bar-value").textContent =
      showAllValues || i === maxIndex ? pctText : "";
  });
}

function setRotationAngle(probHidden) {
  const angleDeg = (Math.asin(Math.sqrt(Math.min(1, probHidden))) * 180) / Math.PI;
  stateVector.style.transform = `rotate(${-angleDeg}deg)`;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function xForN(n) {
  const minLog = Math.log2(SPEEDUP_CHART_N_VALUES[0]);
  const maxLog = Math.log2(SPEEDUP_CHART_N_VALUES[SPEEDUP_CHART_N_VALUES.length - 1]);
  const t = (Math.log2(n) - minLog) / (maxLog - minLog);
  return CHART.left + t * (CHART.right - CHART.left);
}

function yForValue(value, maxValue) {
  const t = value / maxValue;
  return CHART.bottom - t * (CHART.bottom - CHART.top);
}

function updateSpeedupPanel(nAnswers, iterations) {
  const classicalPct = 100;
  const quantumPct = Math.max(2, (iterations / nAnswers) * 100);
  classicalBar.style.width = `${classicalPct}%`;
  quantumBar.style.width = `${quantumPct}%`;
  classicalValue.textContent = `up to ${nAnswers}`;
  quantumValue.textContent = `${iterations}`;
  speedupCaption.textContent =
    `With ${nAnswers} possible answers, a classical brute-force search could need up to ` +
    `${nAnswers} guesses (checking one at a time) — Grover's algorithm found it in just ` +
    `${iterations} iteration${iterations === 1 ? "" : "s"}.`;

  const maxN = SPEEDUP_CHART_N_VALUES[SPEEDUP_CHART_N_VALUES.length - 1];
  const classicalPoints = SPEEDUP_CHART_N_VALUES.map(
    (n) => `${xForN(n)},${yForValue(n, maxN)}`
  ).join(" ");
  const quantumPoints = SPEEDUP_CHART_N_VALUES.map(
    (n) => `${xForN(n)},${yForValue(optimalIterations(n), maxN)}`
  ).join(" ");
  classicalCurve.setAttribute("points", classicalPoints);
  quantumCurve.setAttribute("points", quantumPoints);

  classicalMarker.setAttribute("cx", xForN(nAnswers));
  classicalMarker.setAttribute("cy", yForValue(nAnswers, maxN));

  quantumMarker.setAttribute("cx", xForN(nAnswers));
  quantumMarker.setAttribute("cy", yForValue(iterations, maxN));
}

async function animateSteps(steps, hiddenIndex, iterations) {
  for (let k = 0; k < steps.length; k++) {
    status.textContent =
      k === 0
        ? "Starting from the uniform superposition (before any Grover iteration)..."
        : `Iteration ${k} of ${iterations}: oracle flips the hidden answer's sign, diffuser inverts about the mean...`;
    setBarHeights(steps[k]);
    setRotationAngle(steps[k][hiddenIndex]);
    await sleep(STEP_PAUSE_MS);
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  shakeBtn.disabled = true;
  stage.hidden = true;
  circuits.hidden = true;
  speedup.hidden = true;
  reveal.hidden = true;
  status.textContent = "Shaking the ball...";
  ball.classList.add("shaking");

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: questionInput.value,
        qubits: selectedQubits,
      }),
    });

    if (!res.ok) {
      throw new Error((await res.json()).detail || "Something went wrong");
    }

    const data = await res.json();

    ball.classList.remove("shaking");
    status.textContent = `Hidden answer picked. Running Grover's algorithm (${data.iterations} iteration${data.iterations === 1 ? "" : "s"})...`;

    shakeDiagram.textContent = data.shake_circuit;
    groverDiagram.textContent = data.grover_circuit;
    circuits.hidden = false;

    updateSpeedupPanel(data.n_answers, data.iterations);
    speedup.hidden = false;

    buildBars(data.n_answers, data.answers, data.hidden_index);
    stage.hidden = false;

    await sleep(STEP_PAUSE_MS);
    await animateSteps(data.steps, data.hidden_index, data.iterations);

    revealedText.textContent = `🎱 ${data.answers[data.revealed_index]}`;
    hitRateEl.textContent = `Hidden answer measured ${Math.round(data.hit_rate * 100)}% of ${data.shots} shots.`;
    reveal.hidden = false;
    status.textContent = "";
  } catch (err) {
    ball.classList.remove("shaking");
    status.textContent = `Error: ${err.message}`;
  } finally {
    shakeBtn.disabled = false;
  }
});
