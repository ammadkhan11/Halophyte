from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

NUMERIC_FIELDS = [
    "gr50_avg",
    "na_shoot",
    "na_root",
    "cl_shoot",
    "cl_root",
    "k_shoot",
    "k_root",
]

MECHANISM_ENCODER = {"Non-Secreting": 0, "Salt-Secreting": 1}

CSV_CANDIDATES = [
    PROJECT_ROOT / "ml" / "data" / "halophyte_grass_library.csv",
    PROJECT_ROOT / "data" / "halophyte_grass_library.csv",
    PROJECT_ROOT / "halophyte_grass_library.csv",
]

TS_CANDIDATES = [
    PROJECT_ROOT / "src" / "data" / "grassLibraryData.ts",
    PROJECT_ROOT / "grassLibraryData.ts",
]

MODEL_BUNDLE_PATH = PROJECT_ROOT / "ml" / "models" / "best_model_bundle.joblib"
MODEL_COMPARISON_PATH = PROJECT_ROOT / "ml" / "models" / "model_comparison_results.csv"
MODEL_METRICS_PATH = PROJECT_ROOT / "ml" / "models" / "model_metrics_summary.json"


def snake_case_column(name: str) -> str:
    text = str(name).strip().lower()
    replacements = {
        "+": "",
        "cl−": "cl",
        "cl-": "cl",
        "na+": "na",
        "k+": "k",
        "/": "_",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def clean_numeric(value: Any) -> float:
    if pd.isna(value):
        return float("nan")
    if isinstance(value, (int, float, np.number)):
        return float(value)
    text = str(value).replace(",", "").replace("*", "").strip()
    numbers = re.findall(r"-?\d+(?:\.\d+)?", text)
    return float(numbers[0]) if numbers else float("nan")


def parse_numeric_range(value: Any) -> tuple[float, float, float]:
    if pd.isna(value):
        return float("nan"), float("nan"), float("nan")
    if isinstance(value, (int, float, np.number)):
        number = float(value)
        return number, number, number
    text = str(value).replace(",", "").replace("*", "").strip()
    numbers = [float(item) for item in re.findall(r"-?\d+(?:\.\d+)?", text)]
    if not numbers:
        return float("nan"), float("nan"), float("nan")
    if len(numbers) == 1:
        return numbers[0], numbers[0], numbers[0]
    minimum = min(numbers[0], numbers[1])
    maximum = max(numbers[0], numbers[1])
    return minimum, maximum, (minimum + maximum) / 2


def normalize_mechanism(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().lower().replace("_", "-").replace(" ", "-")
    if text.startswith("non"):
        return "Non-Secreting"
    if "salt" in text and "secreting" in text:
        return "Salt-Secreting"
    if text in {"1", "true", "yes"}:
        return "Salt-Secreting"
    if text in {"0", "false", "no"}:
        return "Non-Secreting"
    return str(value).strip()


def first_existing_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    for alias in aliases:
        candidate = snake_case_column(alias)
        if candidate in df.columns:
            return candidate
    return None


def require_column(df: pd.DataFrame, canonical_name: str, aliases: list[str]) -> str:
    column = first_existing_column(df, aliases)
    if column is None:
        raise KeyError(f"Missing required column for {canonical_name}. Tried aliases: {aliases}")
    return column


def load_from_typescript(ts_path: Path) -> pd.DataFrame:
    text = ts_path.read_text(encoding="utf-8")
    match = re.search(r"grassLibraryData[^=]*=\s*(\[.*?\n\]);", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Could not locate grassLibraryData array in {ts_path}")
    return pd.DataFrame(json.loads(match.group(1)))


def load_raw_dataset() -> tuple[pd.DataFrame, Path]:
    for path in CSV_CANDIDATES:
        if path.exists():
            return pd.read_csv(path), path

    for path in TS_CANDIDATES:
        if path.exists():
            df = load_from_typescript(path)
            local_csv = PROJECT_ROOT / "backend" / "halophyte_grass_library_backend.csv"
            df.to_csv(local_csv, index=False)
            return df, path

    searched = [str(path) for path in CSV_CANDIDATES + TS_CANDIDATES]
    raise FileNotFoundError(f"No cleaned dataset found. Searched: {searched}")


def clean_dataset(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df.columns = [snake_case_column(column) for column in df.columns]

    aliases = {
        "species": ["species", "grass_species", "scientific_name", "species_full_name"],
        "common_name": ["common_name", "common"],
        "mechanism": ["mechanism", "salt_mechanism"],
        "gr50_min": ["gr50_min", "gr50_min_ds_m", "gr50_minimum"],
        "gr50_max": ["gr50_max", "gr50_max_ds_m", "gr50_maximum"],
        "gr50_avg": ["gr50_avg", "gr50_average", "gr50_avg_ds_m"],
        "gr50_range": ["gr50", "gr50_display", "gr50_range"],
        "na_shoot": ["na_shoot", "na_shoot_mmol_kg_dw", "na_shoot_content"],
        "na_root": ["na_root", "na_root_mmol_kg_dw", "na_root_content"],
        "cl_shoot": ["cl_shoot", "cl_shoot_mmol_kg_dw", "cl_shoot_content"],
        "cl_root": ["cl_root", "cl_root_mmol_kg_dw", "cl_root_content"],
        "k_shoot": ["k_shoot", "k_shoot_mmol_kg_dw", "k_shoot_content"],
        "k_root": ["k_root", "k_root_mmol_kg_dw", "k_root_content"],
    }

    clean_df = pd.DataFrame(
        {
            "species": df[require_column(df, "species", aliases["species"])].astype(str).str.strip(),
            "common_name": df[require_column(df, "common_name", aliases["common_name"])].astype(str).str.strip(),
            "mechanism": df[require_column(df, "mechanism", aliases["mechanism"])].apply(normalize_mechanism),
        }
    )

    for field in ["na_shoot", "na_root", "cl_shoot", "cl_root", "k_shoot", "k_root"]:
        clean_df[field] = df[require_column(df, field, aliases[field])].apply(clean_numeric)

    gr50_min_col = first_existing_column(df, aliases["gr50_min"])
    gr50_max_col = first_existing_column(df, aliases["gr50_max"])
    gr50_avg_col = first_existing_column(df, aliases["gr50_avg"])
    gr50_range_col = first_existing_column(df, aliases["gr50_range"])

    if gr50_min_col and gr50_max_col:
        clean_df["gr50_min"] = df[gr50_min_col].apply(clean_numeric)
        clean_df["gr50_max"] = df[gr50_max_col].apply(clean_numeric)
    elif gr50_range_col:
        parsed = df[gr50_range_col].apply(parse_numeric_range)
        clean_df["gr50_min"] = parsed.apply(lambda item: item[0])
        clean_df["gr50_max"] = parsed.apply(lambda item: item[1])
    else:
        raise KeyError("GR50 fields are missing from the dataset.")

    clean_df["gr50_avg"] = (
        df[gr50_avg_col].apply(clean_numeric)
        if gr50_avg_col
        else clean_df[["gr50_min", "gr50_max"]].mean(axis=1)
    )
    clean_df["mechanism_encoded"] = clean_df["mechanism"].map(MECHANISM_ENCODER)

    required = ["species", "common_name", "mechanism", "mechanism_encoded", "gr50_min", "gr50_max"] + NUMERIC_FIELDS
    clean_df = clean_df[required].dropna(subset=["mechanism_encoded"] + NUMERIC_FIELDS).reset_index(drop=True)
    return clean_df


def load_model_bundle() -> dict[str, Any] | None:
    if not MODEL_BUNDLE_PATH.exists():
        return None
    try:
        return joblib.load(MODEL_BUNDLE_PATH)
    except Exception:
        return None


class LoadedResources:
    def __init__(self) -> None:
        self.raw_df, self.dataset_path = load_raw_dataset()
        self.dataset = clean_dataset(self.raw_df)
        self.model_bundle = load_model_bundle()

    @property
    def dataset_loaded(self) -> bool:
        return not self.dataset.empty

    @property
    def model_loaded(self) -> bool:
        return self.model_bundle is not None


resources = LoadedResources()
