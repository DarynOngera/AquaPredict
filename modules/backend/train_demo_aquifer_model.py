"""Train the AquaPredict synthetic-label aquifer demo model.

This produces a demonstration-only classifier from simulated Kenya-like
hydro-climatic records. It is not validated ground-truth and must never be
used for drilling or water-resource decisions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split


FEATURE_NAMES = [
    "elevation",
    "slope",
    "twi",
    "precip_mean",
    "temp_mean",
    "ndvi",
    "landcover",
]


def generate_synthetic_records(samples: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Generate Kenya-like environmental features and synthetic aquifer labels.

    The distributions distinguish coastal, lake-basin, highland/rift, and arid
    northern conditions. Labels are probabilistic functions of hydrological
    plausibility, then deliberately perturbed with noise so a model cannot
    simply memorize a rule.
    """
    rng = np.random.default_rng(seed)
    region = rng.choice(4, size=samples, p=[0.23, 0.27, 0.30, 0.20])

    elevation_means = np.array([90, 1150, 1950, 800])
    precipitation_means = np.array([1050, 1400, 1050, 420])
    temperature_means = np.array([26.5, 23.5, 18.5, 28.0])
    ndvi_means = np.array([0.42, 0.62, 0.48, 0.20])

    elevation = np.clip(rng.normal(elevation_means[region], 280), 0, 3600)
    slope = np.clip(rng.gamma(2.1, 3.0, samples) + (region == 2) * 2.0, 0, 45)
    precipitation = np.clip(rng.normal(precipitation_means[region], 230), 150, 2200)
    temperature = np.clip(rng.normal(temperature_means[region], 2.2), 12, 34)
    ndvi = np.clip(rng.normal(ndvi_means[region], 0.12), 0.02, 0.90)
    twi = np.clip(5.5 + precipitation / 270 + ndvi * 3 - slope / 14 + rng.normal(0, 1.4, samples), 2, 18)
    landcover = rng.choice(np.array([10, 20, 30, 40, 50, 60, 70]), size=samples,
                         p=[0.08, 0.22, 0.19, 0.08, 0.22, 0.14, 0.07])

    # Higher wetness, vegetation, rainfall and permeable land cover imply a
    # higher synthetic aquifer probability; extreme terrain reduces it.
    permeable_cover = np.isin(landcover, [20, 30, 40, 60]).astype(float)
    log_odds = (
        -3.4
        + 0.20 * twi
        + 0.0017 * precipitation
        + 1.7 * ndvi
        + 0.65 * permeable_cover
        - 0.035 * slope
        - 0.00000022 * (elevation - 1450) ** 2
        + rng.normal(0, 0.75, samples)
    )
    probability = 1 / (1 + np.exp(-log_odds))
    labels = rng.binomial(1, probability)

    features = np.column_stack((elevation, slope, twi, precipitation, temperature, ndvi, landcover))
    return features, labels


def main() -> None:
    parser = argparse.ArgumentParser(description="Train synthetic AquaPredict aquifer demo model")
    parser.add_argument("--output", type=Path, default=Path("/output/aquifer_classifier.pkl"))
    parser.add_argument("--samples", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    x, y = generate_synthetic_records(args.samples, args.seed)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=args.seed, stratify=y
    )
    model = RandomForestClassifier(
        n_estimators=350,
        max_depth=12,
        min_samples_leaf=4,
        class_weight="balanced",
        random_state=args.seed,
        n_jobs=-1,
    )
    model.fit(x_train, y_train)

    probabilities = model.predict_proba(x_test)[:, 1]
    metadata = {
        "model_type": "RandomForestClassifier",
        "purpose": "synthetic-label demonstration only",
        "data_provenance": "Kenya-like simulated hydro-climatic features and probabilistic synthetic labels",
        "not_for_operational_use": True,
        "feature_names": FEATURE_NAMES,
        "training_samples": int(len(x_train)),
        "test_samples": int(len(x_test)),
        "positive_class_rate": round(float(y.mean()), 4),
        "holdout_accuracy": round(float(accuracy_score(y_test, model.predict(x_test))), 4),
        "holdout_roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "random_seed": args.seed,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.output)
    args.output.with_name("aquifer_classifier_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
