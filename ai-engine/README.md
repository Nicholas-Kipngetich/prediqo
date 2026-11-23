# Prediqo AI engine

Placeholder for Phase 5. Architecture and validation plan:
`documentation/ai-ml/06-ai-ml-architecture.md`.

Planned modules:

```
data/         raw data loaders and normalisation
features/     as-of feature builder (strictly pre-kickoff)
models/       Poisson + Dixon-Coles, Elo, XGBoost, ensemble, calibration
evaluation/   chronological splits, walk-forward, Brier/log loss, drift
tests/        leakage, reproducibility, probability validation
```

No numerical prediction code exists yet. Recommendations from Phase 0 stand:
statistical models produce all probabilities; the explanation layer is deterministic
in v1 and never fabricates statistics.
