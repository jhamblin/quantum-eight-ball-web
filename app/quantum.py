"""Grover's algorithm circuit-building, vendored from the quantum-eight-ball
CLI (https://github.com/jhamblin/quantum-eight-ball/blob/main/eight_ball.py),
plus a step-by-step amplitude readout used to animate the "reveal" on the
website. See that repo's README for the full derivation of every piece here.
"""

import math
from typing import Dict, List

import numpy as np
from braket.circuits import Circuit
from braket.devices import LocalSimulator

DEFAULT_QUBITS = 3
MAX_QUBITS = 5  # keeps curated flavor text and the per-request simulation fast

CURATED_ANSWERS = [
    "It is certain",
    "Without a doubt",
    "You may rely on it",
    "Ask again later",
    "Cannot predict now",
    "Don't count on it",
    "My sources say no",
    "Outlook not so good",
    "It is decidedly so",
    "Yes, definitely",
    "As I see it, yes",
    "Most likely",
    "Outlook good",
    "Signs point to yes",
    "Yes",
    "Reply hazy, try again",
    "Better not tell you now",
    "Concentrate and ask again",
    "The odds are impossible to calculate",
    "Very doubtful",
    "Signs point to no",
    "Highly unlikely",
    "The stars say no",
    "Chances are slim",
    "My reply is no",
    "Better not count on it",
    "The qubits are undecided",
    "Superposition says maybe",
    "Ask again after decoherence",
    "The wavefunction has not collapsed yet",
    "Entangled with another answer, unclear",
    "Only in a parallel universe",
]


def get_answers(n_qubits: int) -> List[str]:
    return CURATED_ANSWERS[: 2**n_qubits]


def optimal_iterations(n_items: int, n_marked: int = 1) -> int:
    theta = math.asin(math.sqrt(n_marked / n_items))
    return round((math.pi / (4 * theta)) - 0.5)


def ancilla_count(n_controls: int) -> int:
    return max(0, n_controls - 2)


def multi_controlled_x(
    circuit: Circuit, controls: List[int], target: int, ancillas: List[int]
) -> None:
    k = len(controls)
    if k == 0:
        circuit.x(target)
        return
    if k == 1:
        circuit.cnot(controls[0], target)
        return
    if k == 2:
        circuit.ccnot(controls[0], controls[1], target)
        return

    assert len(ancillas) == k - 2, "need exactly k-2 ancilla qubits for k controls"

    chain = [controls[0], controls[1]] + ancillas
    circuit.ccnot(chain[0], chain[1], chain[2])
    for i in range(2, k - 1):
        circuit.ccnot(controls[i], chain[i], chain[i + 1])
    circuit.ccnot(controls[k - 1], chain[-1], target)
    for i in reversed(range(2, k - 1)):
        circuit.ccnot(controls[i], chain[i], chain[i + 1])
    circuit.ccnot(chain[0], chain[1], chain[2])


def phase_flip_all_ones(
    circuit: Circuit, qubits: List[int], ancillas: List[int]
) -> None:
    if len(qubits) == 1:
        circuit.z(qubits[0])
        return

    *controls, target = qubits
    circuit.h(target)
    multi_controlled_x(circuit, controls, target, ancillas)
    circuit.h(target)


def oracle(target_bits: str, qubits: List[int], ancillas: List[int]) -> Circuit:
    circuit = Circuit()
    zero_positions = [qubits[i] for i, bit in enumerate(target_bits) if bit == "0"]

    for q in zero_positions:
        circuit.x(q)
    phase_flip_all_ones(circuit, qubits, ancillas)
    for q in zero_positions:
        circuit.x(q)

    return circuit


def diffuser(qubits: List[int], ancillas: List[int]) -> Circuit:
    circuit = Circuit()
    for q in qubits:
        circuit.h(q)
    for q in qubits:
        circuit.x(q)
    phase_flip_all_ones(circuit, qubits, ancillas)
    for q in qubits:
        circuit.x(q)
    for q in qubits:
        circuit.h(q)
    return circuit


def build_shake_circuit(qubits: List[int]) -> Circuit:
    circuit = Circuit()
    for q in qubits:
        circuit.h(q)
    return circuit


def shake(device, qubits: List[int]) -> str:
    """One quantum coin-flip: uniform superposition + a single measurement."""
    circuit = build_shake_circuit(qubits)
    result = device.run(circuit, shots=1).result()
    return "".join(str(bit) for bit in result.measurements[0])


def probabilities_per_answer(
    statevector: np.ndarray, n_answers: int, n_ancillas: int
) -> List[float]:
    """Collapse a full statevector (answer qubits + ancillas) down to one
    probability per answer, by summing over every ancilla bit pattern."""
    probs = [0.0] * n_answers
    block = 2**n_ancillas
    for answer_index in range(n_answers):
        start = answer_index * block
        probs[answer_index] = float(
            np.sum(np.abs(statevector[start : start + block]) ** 2)
        )
    return probs


def _touch_all_qubits(circuit: Circuit, qubits: List[int]) -> None:
    """Force every qubit (including ancillas) into the circuit's register
    with an identity gate, so the simulator's qubit count -- and therefore
    the statevector's dimension -- stays fixed even on iteration 0, when no
    oracle/diffuser gate would otherwise touch the ancillas at all."""
    for q in qubits:
        circuit.i(q)


def simulate_amplitude_steps(
    target_bits: str, n_qubits: int, ancillas: List[int], iterations: int
) -> List[List[float]]:
    """Run the Grover circuit on the local simulator once per iteration count
    (0..iterations), reading out the exact statevector each time, to animate
    how probability piles onto the hidden answer step by step."""
    device = LocalSimulator()
    main_qubits = list(range(n_qubits))
    n_answers = 2**n_qubits
    steps = []

    for k in range(iterations + 1):
        circuit = Circuit()
        _touch_all_qubits(circuit, main_qubits + ancillas)
        for q in main_qubits:
            circuit.h(q)
        for _ in range(k):
            circuit.add_circuit(oracle(target_bits, main_qubits, ancillas))
            circuit.add_circuit(diffuser(main_qubits, ancillas))
        circuit.state_vector()
        result = device.run(circuit, shots=0).result()
        sv = np.asarray(result.values[0])
        steps.append(probabilities_per_answer(sv, n_answers, len(ancillas)))

    return steps


def run_final_measurement(
    target_bits: str, n_qubits: int, ancillas: List[int], iterations: int, shots: int
) -> Dict[str, int]:
    """The real, shot-based measurement of the fully-amplified circuit,
    matching what eight_ball.py's CLI reports -- for the histogram shown
    alongside the amplitude animation."""
    device = LocalSimulator()
    main_qubits = list(range(n_qubits))

    circuit = Circuit()
    _touch_all_qubits(circuit, main_qubits + ancillas)
    for q in main_qubits:
        circuit.h(q)
    for _ in range(iterations):
        circuit.add_circuit(oracle(target_bits, main_qubits, ancillas))
        circuit.add_circuit(diffuser(main_qubits, ancillas))

    result = device.run(circuit, shots=shots).result()
    counts: Dict[str, int] = {}
    for bitstring, count in result.measurement_counts.items():
        answer_bits = bitstring[:n_qubits]
        counts[answer_bits] = counts.get(answer_bits, 0) + count
    return counts


def ask(question: str, n_qubits: int, shots: int = 1000) -> dict:
    """End to end: shake, then Grover, returning everything the frontend
    needs to animate the reveal."""
    if not (1 <= n_qubits <= MAX_QUBITS):
        raise ValueError(f"qubits must be between 1 and {MAX_QUBITS}")

    device = LocalSimulator()
    main_qubits = list(range(n_qubits))
    n_ancillas = ancilla_count(n_qubits - 1)
    ancillas = list(range(n_qubits, n_qubits + n_ancillas))

    target_bits = shake(device, main_qubits)
    target_index = int(target_bits, 2)

    iterations = optimal_iterations(2**n_qubits)
    steps = simulate_amplitude_steps(target_bits, n_qubits, ancillas, iterations)
    counts = run_final_measurement(target_bits, n_qubits, ancillas, iterations, shots)

    answers = get_answers(n_qubits)
    revealed_bits = max(counts, key=counts.get)
    revealed_index = int(revealed_bits, 2)

    return {
        "question": question,
        "qubits": n_qubits,
        "n_answers": 2**n_qubits,
        "answers": answers,
        "hidden_index": target_index,
        "hidden_bits": target_bits,
        "iterations": iterations,
        "steps": steps,
        "shots": shots,
        "counts": counts,
        "revealed_index": revealed_index,
        "hit_rate": counts.get(target_bits, 0) / shots,
    }
