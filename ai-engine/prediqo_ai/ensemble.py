"""Validation-weighted ensemble with probability calibration."""

from dataclasses import dataclass

from prediqo_ai.evaluation import probability_vector_is_valid
from prediqo_ai.poisson import to_basis_points


@dataclass(frozen=True)
class MarketPrediction:
    market: str
    probabilities_bp: dict[str, int]
    selected_outcome: str
    model_version: str
    data_quality_ok: bool


def combine_1x2(
    poisson: dict[str, float],
    elo: dict[str, float],
    weight_poisson: float = 0.6,
    temperature: float = 1.0,
) -> dict[str, float]:
    """Blend two 1X2 distributions with a temperature calibration."""
    weight_poisson = min(max(weight_poisson, 0.0), 1.0)
    blended = {
        key: weight_poisson * poisson[key] + (1 - weight_poisson) * elo[key]
        for key in ("home", "draw", "away")
    }
    if temperature == 1.0:
        calibrated = blended
    else:
        powered = {key: max(value, 1e-9) ** (1 / temperature) for key, value in blended.items()}
        total = sum(powered.values())
        calibrated = {key: value / total for key, value in powered.items()}
    if not probability_vector_is_valid(calibrated, tolerance=1e-4):
        raise ValueError("Ensemble produced an invalid probability vector.")
    return calibrated


def publish_market(
    market: str,
    probabilities: dict[str, float],
    model_version: str,
    data_quality_ok: bool = True,
) -> MarketPrediction:
    """Convert probabilities to integer basis points with an argmax selection."""
    total = sum(probabilities.values())
    normalised = {key: value / total for key, value in probabilities.items()} if total else {}
    if not probability_vector_is_valid(normalised, tolerance=1e-4):
        raise ValueError(f"Cannot publish market {market}: invalid probabilities.")
    basis_points = to_basis_points(normalised)
    selected = max(basis_points, key=basis_points.get)
    return MarketPrediction(
        market=market,
        probabilities_bp=basis_points,
        selected_outcome=selected,
        model_version=model_version,
        data_quality_ok=data_quality_ok,
    )
