"""Model evaluation metrics and suppression helpers."""

import math


def brier_score(probabilities: list[float], outcomes: list[int]) -> float:
    if len(probabilities) != len(outcomes) or not outcomes:
        raise ValueError("Aligned, non-empty inputs are required.")
    return sum((p - o) ** 2 for p, o in zip(probabilities, outcomes, strict=False)) / len(outcomes)


def log_loss(probabilities: list[float], outcomes: list[int], eps: float = 1e-12) -> float:
    if len(probabilities) != len(outcomes) or not outcomes:
        raise ValueError("Aligned, non-empty inputs are required.")
    total = 0.0
    for p, outcome in zip(probabilities, outcomes, strict=False):
        clipped = min(max(p, eps), 1 - eps)
        target = 1 if outcome else 0
        total -= target * math.log(clipped) + (1 - target) * math.log(1 - clipped)
    return total / len(outcomes)


def accuracy(probabilities: list[float], outcomes: list[int]) -> float:
    if len(probabilities) != len(outcomes) or not outcomes:
        raise ValueError("Aligned, non-empty inputs are required.")
    correct = sum(1 for p, o in zip(probabilities, outcomes, strict=False) if int(p >= 0.5) == o)
    return correct / len(outcomes)


def calibration_bins(
    probabilities: list[float], outcomes: list[int], bins: int = 10
) -> list[dict[str, float | int]]:
    result = []
    for index in range(bins):
        low = index / bins
        high = (index + 1) / bins
        pairs = [
            (p, o)
            for p, o in zip(probabilities, outcomes, strict=False)
            if low <= p < high or (index == bins - 1 and p == 1.0)
        ]
        if not pairs:
            continue
        result.append(
            {
                "bin": index,
                "count": len(pairs),
                "mean_probability": sum(p for p, _ in pairs) / len(pairs),
                "observed_rate": sum(o for _, o in pairs) / len(pairs),
            }
        )
    return result


def probability_vector_is_valid(values: dict[str, float], tolerance: float = 1e-6) -> bool:
    total = sum(values.values())
    return (
        bool(values)
        and all(0 <= value <= 1 for value in values.values())
        and abs(total - 1) < tolerance
    )
