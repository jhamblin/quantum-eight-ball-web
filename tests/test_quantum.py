import math

import pytest

from app import quantum


def test_optimal_iterations_matches_known_values():
    # From the quantum-eight-ball README's worked table.
    assert quantum.optimal_iterations(8) == 2
    assert quantum.optimal_iterations(16) == 3
    assert quantum.optimal_iterations(32) == 4


def test_ancilla_count():
    assert quantum.ancilla_count(2) == 0
    assert quantum.ancilla_count(3) == 1
    assert quantum.ancilla_count(4) == 2


def test_get_answers_returns_exact_count():
    for n_qubits in range(1, quantum.MAX_QUBITS + 1):
        answers = quantum.get_answers(n_qubits)
        assert len(answers) == 2**n_qubits


def test_probabilities_per_answer_marginalizes_ancillas():
    import numpy as np

    # 1 answer qubit, 1 ancilla: amplitude spread across answer=1 with the
    # ancilla in both |0> and |1>, should combine into one answer bucket.
    sv = np.array([0, 0, 0.6, 0.8])  # |10>, |11> carry all the amplitude
    probs = quantum.probabilities_per_answer(sv, n_answers=2, n_ancillas=1)
    assert probs[0] == pytest.approx(0.0)
    assert probs[1] == pytest.approx(0.36 + 0.64)


@pytest.mark.parametrize("n_qubits", [3, 4, 5])
def test_simulate_amplitude_steps_starts_uniform_and_amplifies(n_qubits):
    n_answers = 2**n_qubits
    ancillas = list(range(n_qubits, n_qubits + quantum.ancilla_count(n_qubits - 1)))
    target_bits = "0" * n_qubits
    iterations = quantum.optimal_iterations(n_answers)

    steps = quantum.simulate_amplitude_steps(target_bits, n_qubits, ancillas, iterations)

    assert len(steps) == iterations + 1
    for p in steps[0]:
        assert p == pytest.approx(1 / n_answers, abs=1e-6)
    assert sum(steps[0]) == pytest.approx(1.0)

    final = steps[-1]
    assert sum(final) == pytest.approx(1.0, abs=1e-6)
    assert final[0] > 0.9  # target_bits == "00...0" -> index 0


def test_run_final_measurement_counts_sum_to_shots():
    shots = 500
    circuit = quantum.build_full_grover_circuit(
        target_bits="101", n_qubits=3, ancillas=[], iterations=2
    )
    counts = quantum.run_final_measurement(circuit, n_qubits=3, shots=shots)
    assert sum(counts.values()) == shots
    assert counts.get("101", 0) / shots > 0.8


def test_render_circuit_omits_wide_diagrams():
    circuit = quantum.build_full_grover_circuit(
        target_bits="00000", n_qubits=5, ancillas=[5, 6], iterations=4
    )
    text = quantum.render_circuit(circuit, total_qubits=7)
    assert "too wide to render legibly" in text

    small_circuit = quantum.build_full_grover_circuit(
        target_bits="101", n_qubits=3, ancillas=[], iterations=2
    )
    text = quantum.render_circuit(small_circuit, total_qubits=3)
    assert "too wide" not in text
    assert "q0" in text


def test_ask_end_to_end_smoke():
    result = quantum.ask("Will this work?", n_qubits=3, shots=200)
    assert result["qubits"] == 3
    assert result["n_answers"] == 8
    assert len(result["answers"]) == 8
    assert 0 <= result["hidden_index"] < 8
    assert len(result["steps"]) == result["iterations"] + 1
    assert sum(result["counts"].values()) == 200
    assert result["hit_rate"] > 0.5
    assert "q0" in result["shake_circuit"]
    assert "q0" in result["grover_circuit"]


def test_ask_rejects_out_of_range_qubits():
    with pytest.raises(ValueError):
        quantum.ask("x", n_qubits=quantum.MAX_QUBITS + 1)
