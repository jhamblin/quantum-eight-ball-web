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
  for (let i = 0; i < n; i++) {
    const col = document.createElement("div");
    col.className = "bar-col";

    const bar = document.createElement("div");
    bar.className = "bar" + (i === hiddenIndex ? " is-hidden" : "");
    bar.style.height = "2px";
    bar.title = answers[i];

    const label = document.createElement("div");
    label.className = "bar-label";
    label.textContent = i.toString(2).padStart(Math.log2(n), "0");

    col.appendChild(bar);
    if (n <= 8) col.appendChild(label);
    barsEl.appendChild(col);
  }
}

function setBarHeights(probs) {
  const bars = barsEl.querySelectorAll(".bar");
  bars.forEach((bar, i) => {
    const pct = Math.max(2, probs[i] * 100);
    bar.style.height = `${(pct / 100) * 220}px`;
  });
}

function setRotationAngle(probHidden) {
  const angleDeg = (Math.asin(Math.sqrt(Math.min(1, probHidden))) * 180) / Math.PI;
  stateVector.style.transform = `rotate(${-angleDeg}deg)`;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function animateSteps(steps, hiddenIndex) {
  for (const probs of steps) {
    setBarHeights(probs);
    setRotationAngle(probs[hiddenIndex]);
    await sleep(650);
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  shakeBtn.disabled = true;
  stage.hidden = true;
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

    buildBars(data.n_answers, data.answers, data.hidden_index);
    stage.hidden = false;

    await animateSteps(data.steps, data.hidden_index);

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
