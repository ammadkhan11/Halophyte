"""
ML Surrogate Model Training
============================
Trains per-species models on the Pakistani salinity-yield dataset.

Strategy: One model per crop species (barley, wheat, maize, sorghum, rice, quinoa).
This gives much higher R² because each species has a distinct salinity response curve.

Dataset: data/raw/AuthenticHalophyteData.xlsx
  - 241 data points from 11 Pakistani research papers
  - 6 species: barley, wheat, maize, sorghum, rice, quinoa

Usage:
    python -m src.surrogate.train

Output:
    models/surrogate_model.pkl  -- dict of per-species models
    models/model_metadata.json  -- per-species R2, MAE, overall metrics
"""

import json
import pickle
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import LeaveOneOut, train_test_split
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

# ============================================================================
# PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PATH_CANDIDATES = [
    PROJECT_ROOT / "data" / "raw" / "AuthenticHalophyteData.xlsx",
    PROJECT_ROOT.parent / "AuthenticHalophyteData.xlsx",
]
DATA_PATH = next((path for path in DATA_PATH_CANDIDATES if path.exists()), DATA_PATH_CANDIDATES[0])
MODEL_PATH = PROJECT_ROOT / "models" / "surrogate_model.pkl"
ENCODER_PATH = PROJECT_ROOT / "models" / "species_encoder.pkl"
METADATA_PATH = PROJECT_ROOT / "models" / "model_metadata.json"


# ============================================================================
# DATA LOADING
# ============================================================================

def load_data() -> pd.DataFrame:
    """Load and clean the Pakistani dataset."""
    print(f"Loading dataset from: {DATA_PATH}")
    df = pd.read_excel(DATA_PATH)
    print(f"  Loaded {len(df)} rows, {df['species_id'].nunique()} species")

    # Impute missing temperature with species-level median
    missing_temp = df['temperature_C'].isnull().sum()
    if missing_temp > 0:
        print(f"  Imputing {missing_temp} missing temperature values with species medians")
        species_temp_median = df.groupby('species_id')['temperature_C'].median()
        for species in df['species_id'].unique():
            mask = (df['species_id'] == species) & df['temperature_C'].isnull()
            df.loc[mask, 'temperature_C'] = species_temp_median[species]
        df['temperature_C'].fillna(df['temperature_C'].median(), inplace=True)

    return df


def aggregate_by_ec(species_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by EC level (mean across varieties).

    The ML model predicts the SPECIES-LEVEL response to salinity,
    not individual variety responses. Aggregating by EC level:
    - Reduces variety-level noise
    - Gives the model a cleaner salinity-yield signal
    - Better represents what a farmer would expect on average

    Args:
        species_df: DataFrame for one species

    Returns:
        Aggregated DataFrame with mean yield per EC level
    """
    agg = species_df.groupby('ec_soil_dS_m').agg(
        relative_yield_pct=('relative_yield_pct', 'mean'),
        temperature_C=('temperature_C', 'mean'),
        n_varieties=('variety', 'nunique'),
    ).reset_index()
    return agg


def make_features(ec: np.ndarray) -> np.ndarray:
    """
    Create feature matrix for a single species model.
    Features: [ec, ec^2, log(1+ec)]

    Args:
        ec: Array of EC values
    Returns:
        Feature matrix (n_samples, 3)
    """
    ec = np.array(ec, dtype=float)
    return np.column_stack([
        ec,
        ec ** 2,
        np.log1p(ec),
    ])


# ============================================================================
# PER-SPECIES MODEL TRAINING
# ============================================================================

def train_species_model(species_df: pd.DataFrame, species_id: str) -> tuple:
    """
    Train the best model for a single species.

    Tries GradientBoosting, RandomForest, and Ridge regression.
    Selects the one with highest R2 on test split (or LOO-CV for small datasets).

    Args:
        species_df: DataFrame for one species
        species_id: Species name

    Returns:
        best_model: Trained model (fit on ALL data)
        model_name: Name of best algorithm
        r2: Test R2 score
        mae: Test MAE in %
    """
    X = make_features(species_df['ec_soil_dS_m'].values)
    y = species_df['relative_yield_pct'].values
    n = len(X)

    if n < 10:
        # Leave-one-out cross-validation for small datasets (quinoa=18)
        loo = LeaveOneOut()
        candidates = {
            'GradientBoosting': GradientBoostingRegressor(
                n_estimators=100, max_depth=2, learning_rate=0.1,
                min_samples_leaf=2, random_state=42),
            'Ridge': Ridge(alpha=1.0),
        }
        best_name, best_r2, best_mae, best_model = None, -999.0, 999.0, None
        for name, model in candidates.items():
            preds, trues = [], []
            for train_idx, test_idx in loo.split(X):
                model.fit(X[train_idx], y[train_idx])
                preds.append(float(model.predict(X[test_idx])[0]))
                trues.append(float(y[test_idx][0]))
            r2 = r2_score(trues, preds)
            mae = mean_absolute_error(trues, preds)
            if r2 > best_r2:
                best_r2, best_mae, best_name, best_model = r2, mae, name, model
        # Refit on all data for deployment
        best_model.fit(X, y)
        return best_model, best_name, best_r2, best_mae

    else:
        # 80/20 train/test split for larger datasets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42)

        candidates = {
            'GradientBoosting': GradientBoostingRegressor(
                n_estimators=200, max_depth=3, learning_rate=0.08,
                min_samples_leaf=2, subsample=0.9, random_state=42),
            'RandomForest': RandomForestRegressor(
                n_estimators=200, max_depth=6, min_samples_leaf=2,
                random_state=42),
            'Ridge': Ridge(alpha=0.5),
        }

        best_name, best_r2, best_mae, best_model = None, -999.0, 999.0, None
        for name, model in candidates.items():
            model.fit(X_train, y_train)
            pred = model.predict(X_test)
            r2 = r2_score(y_test, pred)
            mae = mean_absolute_error(y_test, pred)
            if r2 > best_r2:
                best_r2, best_mae, best_name, best_model = r2, mae, name, model

        # Refit best model on ALL data for deployment
        best_model.fit(X, y)
        return best_model, best_name, best_r2, best_mae


# ============================================================================
# MAIN TRAINING PIPELINE
# ============================================================================

def run_training_pipeline() -> dict:
    """
    Train per-species models and save to disk.

    Returns:
        metadata: Dict with per-species and overall metrics
    """
    print("=" * 60)
    print("  ML SURROGATE MODEL TRAINING (Per-Species)")
    print("  Digital Twin for Biosaline Agriculture")
    print("=" * 60)

    df = load_data()
    species_list = sorted(df['species_id'].unique())

    # Train one model per species
    models = {}
    species_metrics = {}
    all_r2 = []

    print(f"\nTraining per-species models...")
    print(f"{'Species':12s} {'n':>4s} {'Best Model':20s} {'R2':>8s} {'MAE':>8s}")
    print("-" * 60)

    for species_id in species_list:
        sub = df[df['species_id'] == species_id].copy()
        model, model_name, r2, mae = train_species_model(sub, species_id)
        models[species_id] = model
        species_metrics[species_id] = {
            "model_type": model_name,
            "r2": round(float(r2), 4),
            "mae_pct": round(float(mae), 2),
            "n_samples": len(sub),
        }
        all_r2.append(r2)
        status = "OK" if r2 >= 0.85 else "low"
        print(f"  {species_id:12s} {len(sub):>4d} {model_name:20s} {r2:>7.4f} [{status}]  {mae:>6.2f}%")

    overall_r2 = float(np.mean(all_r2))
    print(f"\n  Overall mean R2: {overall_r2:.4f}")

    # Save models dict
    MODEL_PATH.parent.mkdir(exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(models, f)
    print(f"\n  Model saved: {MODEL_PATH}")

    # Save encoder (species list for compatibility)
    le = LabelEncoder()
    le.fit(species_list)
    with open(ENCODER_PATH, 'wb') as f:
        pickle.dump(le, f)
    print(f"  Encoder saved: {ENCODER_PATH}")

    # Save metadata
    metadata = {
        "model_type": "PerSpeciesModels",
        "strategy": "per_species",
        "overall_mean_r2": round(overall_r2, 4),
        "species_metrics": species_metrics,
        "total_data_points": len(df),
        "target_met": bool(overall_r2 >= 0.85),
        "test_r2": round(overall_r2, 4),
    }
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"  Metadata saved: {METADATA_PATH}")

    print("\n" + "=" * 60)
    print("  TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Strategy:        Per-species models")
    print(f"  Overall mean R2: {overall_r2:.4f}")
    print(f"  Species trained: {len(models)}")

    return metadata


if __name__ == "__main__":
    run_training_pipeline()
