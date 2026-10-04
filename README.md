# Quantum Magic 8-Ball — the website

A browser front end for [quantum-eight-ball](https://github.com/jhamblin/quantum-eight-ball):
ask a question, hit Shake, and watch Grover's algorithm amplify the hidden
answer in real time — a bar per possible answer climbing as each iteration
runs, plus the same evolution drawn as the textbook "rotation toward `|w⟩`"
picture.

Everything runs on [Amazon Braket](https://aws.amazon.com/braket/)'s free
**local simulator** — no AWS account, no credentials, no per-request cost —
so it's safe to point a public site at. (The original CLI can still point
the same circuits at a managed simulator or real QPU; this site intentionally
doesn't, to stay free and instant for visitors.)

## How it works

- `app/quantum.py` vendors the oracle/diffuser/ancilla-ladder circuit code
  from `eight_ball.py` in the CLI repo (see that repo's README for the full
  derivation), plus a `simulate_amplitude_steps()` that re-runs the Grover
  circuit once per iteration count, reading out the exact statevector each
  time with Braket's `state_vector()` result type — that's what the frontend
  animates through.
- `app/main.py` is a small FastAPI app: `POST /api/ask {question, qubits}`
  runs the shake + Grover simulation and returns the per-iteration
  probabilities, the final shot-based histogram, and the revealed answer.
- `static/` is a dependency-free HTML/CSS/JS frontend that animates the bars
  and the rotation vector as the steps come back, then reveals the answer.

Only `--qubits 3/4/5` (8/16/32 answers) are offered, matching the CLI's
hand-written flavor-text answers (`CURATED_ANSWERS`) and keeping each
request's simulation fast.

## Running locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open <http://localhost:8000>.

### Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Related

- [quantum-eight-ball](https://github.com/jhamblin/quantum-eight-ball) — the
  CLI this site is built on, with the full Grover's-algorithm derivation.
- [bell](https://github.com/jhamblin/bell) — a Bell-state "hello world" for
  Braket that introduces qubits, kets, and gates from scratch.
