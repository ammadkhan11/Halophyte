from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from model_loader import MECHANISM_ENCODER, NUMERIC_FIELDS, normalize_mechanism, resources, snake_case_column
from schemas import PredictionRequest


FIELD_ALIASES = {
    "gr50_average": "gr50_avg",
    "gr50_avg_ds_m": "gr50_avg",
    "na_shoot_mmol_kg_dw": "na_shoot",
    "na_root_mmol_kg_dw": "na_root",
    "cl_shoot_mmol_kg_dw": "cl_shoot",
    "cl_root_mmol_kg_dw": "cl_root",
    "k_shoot_mmol_kg_dw": "k_shoot",
    "k_root_mmol_kg_dw": "k_root",
}

PREDICTION_NOTE = "Prediction is an estimated value based on limited dataset patterns."
GRASS_ANCHORED_NOTE = (
    "Grass-based mode uses the selected species profile as the base and adjusts remaining values "
    "using regression patterns learned from the dataset."
)
GRASS_MATCH_NOTE = (
    "Entered value matches the stored dataset value, so predictions remain close to the selected species profile."
)
GRASS_DIFFERENCE_NOTE = (
    "Entered value differs from the stored dataset value, so remaining values are regression-adjusted "
    "from the selected species profile."
)


def normalize_known_field(field: str) -> str:
    normalized = snake_case_column(field)
    return FIELD_ALIASES.get(normalized, normalized)


def get_target_fields(known_field: str) -> list[str]:
    return [field for field in NUMERIC_FIELDS if field != known_field]


def find_species_row(species: str) -> pd.Series:
    query = species.strip().lower()
    dataset = resources.dataset

    exact_match = dataset[
        (dataset["species"].str.lower() == query)
        | (dataset["common_name"].str.lower() == query)
    ]
    if not exact_match.empty:
        return exact_match.iloc[0]

    partial_match = dataset[
        dataset["species"].str.lower().str.contains(query, regex=False, na=False)
        | dataset["common_name"].str.lower().str.contains(query, regex=False, na=False)
    ]
    if not partial_match.empty:
        return partial_match.iloc[0]

    raise ValueError(f"Species not found: {species}")


def build_known_value_comparison(dataset_value: float, user_value: float) -> dict[str, float | None]:
    difference = float(user_value) - float(dataset_value)

    difference_percent = None
    if abs(float(dataset_value)) > 1e-9:
        difference_percent = round((difference / float(dataset_value)) * 100, 2)

    return {
        "dataset_known_value": round(float(dataset_value), 3),
        "user_known_value": round(float(user_value), 3),
        "difference": round(difference, 3),
        "difference_percent": difference_percent,
    }


def resolve_context(request: PredictionRequest) -> tuple[str | None, str, int]:
    if request.mode == "grass_based":
        if not request.species:
            raise ValueError("Select a grass species for grass-based prediction.")
        species_row = find_species_row(request.species)
        mechanism = str(species_row["mechanism"])
        return str(species_row["species"]), mechanism, int(species_row["mechanism_encoded"])

    if not request.mechanism:
        raise ValueError("Select a mechanism for mechanism-based prediction.")

    mechanism = normalize_mechanism(request.mechanism)
    if mechanism not in MECHANISM_ENCODER:
        raise ValueError("Mechanism must be Salt-Secreting or Non-Secreting.")
    return None, mechanism, MECHANISM_ENCODER[mechanism]


def weighted_knn_estimate(
    known_field: str,
    known_value: float,
    mechanism: str,
    neighbors: int = 3,
) -> tuple[dict[str, float], list[dict[str, str]]]:
    dataset = resources.dataset.copy()
    group_df = dataset[dataset["mechanism"] == mechanism].copy()
    if group_df.empty:
        group_df = dataset.copy()

    group_df["distance"] = (group_df[known_field].astype(float) - float(known_value)).abs()
    group_df = group_df.sort_values(["distance", "species"]).head(max(1, min(neighbors, len(group_df))))

    epsilon = 1e-9
    weights = 1 / (group_df["distance"].to_numpy(dtype=float) + epsilon)
    if not np.isfinite(weights).all() or weights.sum() == 0:
        weights = np.ones(len(group_df), dtype=float)
    weights = weights / weights.sum()

    predictions: dict[str, float] = {}
    for field in get_target_fields(known_field):
        values = group_df[field].to_numpy(dtype=float)
        predictions[field] = round(float(np.average(values, weights=weights)), 3)

    similar_grasses = [
        {
            "species": str(row["species"]),
            "common_name": str(row["common_name"]),
            "mechanism": str(row["mechanism"]),
            "similarity_note": f"Nearest match based on {known_field} distance: {float(row['distance']):.3f}",
        }
        for _, row in group_df.iterrows()
    ]
    return predictions, similar_grasses


def regression_slope_for_target(
    known_field: str,
    target_field: str,
    mechanism: str,
    minimum_group_records: int = 3,
) -> tuple[float, str]:
    dataset = resources.dataset.copy()
    same_mechanism = dataset[dataset["mechanism"] == mechanism].dropna(subset=[known_field, target_field])

    if len(same_mechanism) >= minimum_group_records:
        regression_df = same_mechanism
        scope = "same mechanism group"
    else:
        regression_df = dataset.dropna(subset=[known_field, target_field])
        scope = "full dataset"

    if len(regression_df) < 2 or regression_df[known_field].nunique() < 2:
        return 0.0, scope

    X = regression_df[[known_field]].to_numpy(dtype=float)
    y = regression_df[target_field].to_numpy(dtype=float)
    model = Ridge(alpha=1.0)
    model.fit(X, y)
    return float(model.coef_[0]), scope


def species_anchored_regression(
    species_row: pd.Series,
    known_field: str,
    known_value: float,
) -> dict[str, Any]:
    target_fields = get_target_fields(known_field)
    mechanism = str(species_row["mechanism"])
    predictions: dict[str, float] = {}

    dataset_known_value = round(float(species_row[known_field]), 3)
    known_value_comparison = build_known_value_comparison(dataset_known_value, known_value)
    delta = float(known_value_comparison["difference"])
    scopes_used: set[str] = set()

    for field in target_fields:
        base_value = species_row[field]
        if pd.isna(base_value):
            base_value = resources.dataset[field].dropna().mean()

        slope, scope = regression_slope_for_target(
            known_field=known_field,
            target_field=field,
            mechanism=mechanism,
        )
        scopes_used.add(scope)
        predicted_value = float(base_value) + (slope * delta)
        predictions[field] = round(max(0.0, predicted_value), 3)

    note = GRASS_MATCH_NOTE if abs(delta) <= 1e-9 else GRASS_DIFFERENCE_NOTE
    if len(scopes_used) == 1:
        regression_scope = next(iter(scopes_used))
    else:
        regression_scope = "same mechanism group if possible, otherwise full dataset"

    return {
        "mode": "grass_based",
        "species": str(species_row["species"]),
        "mechanism": mechanism,
        "known_field": known_field,
        "known_value": float(known_value),
        "dataset_known_value": dataset_known_value,
        "difference": known_value_comparison["difference"],
        "difference_percent": known_value_comparison["difference_percent"],
        "known_value_comparison": known_value_comparison,
        "calculation_basis": {
            "base_species_profile": True,
            "regression_scope": regression_scope,
            "method": "target = selected species value + regression_slope x known value difference",
        },
        "predictions": predictions,
        "similar_grasses": [],
        "model_used": "Species-anchored regression",
        "note": f"{GRASS_ANCHORED_NOTE} {note}",
    }


def predict_with_saved_model(
    known_field: str,
    known_value: float,
    mechanism_encoded: int,
) -> tuple[dict[str, float], str] | None:
    bundle = resources.model_bundle
    if not bundle:
        return None

    trained_models: dict[str, Any] | None = bundle.get("trained_models")
    selected_models: dict[str, str] | None = bundle.get("selected_best_model_per_known_field")
    target_fields_by_known: dict[str, list[str]] | None = bundle.get("target_fields_by_known_input")

    if not trained_models or not selected_models or not target_fields_by_known:
        return None
    if known_field not in trained_models or known_field not in selected_models:
        return None

    model_name = selected_models[known_field]
    model = trained_models[known_field].get(model_name)
    if model is None:
        return None

    target_fields = target_fields_by_known.get(known_field) or get_target_fields(known_field)
    prediction_input = pd.DataFrame(
        [[mechanism_encoded, float(known_value)]],
        columns=["mechanism_encoded", known_field],
    )
    predicted_values = model.predict(prediction_input)[0]
    predictions = {
        field: round(float(value), 3)
        for field, value in zip(target_fields, predicted_values)
    }
    return predictions, f"Saved notebook model ({model_name})"


def predict(request: PredictionRequest) -> dict[str, Any]:
    known_field = normalize_known_field(request.known_field)
    if known_field not in NUMERIC_FIELDS:
        raise ValueError(f"known_field must be one of: {', '.join(NUMERIC_FIELDS)}")

    known_value = float(request.known_value)

    if request.mode == "grass_based":
        if not request.species:
            raise ValueError("Select a grass species for grass-based prediction.")
        species_row = find_species_row(request.species)
        return species_anchored_regression(
            species_row=species_row,
            known_field=known_field,
            known_value=known_value,
        )

    species, mechanism, _mechanism_encoded = resolve_context(request)

    similar_predictions, similar_grasses = weighted_knn_estimate(
        known_field=known_field,
        known_value=known_value,
        mechanism=mechanism,
    )

    return {
        "mode": request.mode,
        "species": species,
        "mechanism": mechanism,
        "known_field": known_field,
        "known_value": known_value,
        "dataset_known_value": None,
        "known_value_comparison": None,
        "predictions": similar_predictions,
        "similar_grasses": similar_grasses,
        "model_used": "KNN weighted estimation",
        "note": PREDICTION_NOTE,
    }
