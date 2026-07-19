"""
ML Surrogate Model Prediction
===============================
Loads the trained model and produces all 5 outputs for a given scenario.

Outputs:
1. Expected Yield (t/ha)
2. Relative Yield (%)
3. Risk Level (Low/Medium/High)
4. Recommended Irrigation
5. Alternative Halophytes

Usage:
    from src.surrogate.predict import predict_yield

    result = predict_yield("wheat", ec_soil=12.0, temperature=38.0, rainfall_mm=120.0)
"""

import pickle
import warnings
from pathlib import Path
from typing import Optional

import numpy as np

from src.salinity_model.maas_hoffman import full_prediction

warnings.filterwarnings("ignore")

# ============================================================================
# PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "surrogate_model.pkl"
ENCODER_PATH = PROJECT_ROOT / "models" / "species_encoder.pkl"
METADATA_PATH = PROJECT_ROOT / "models" / "model_metadata.json"

# ============================================================================
# MODEL LOADING (cached)
# ============================================================================

_model = None
_encoder = None
_metadata = None


def _load_model():
    """Load model and encoder from disk (cached after first load)."""
    global _model, _encoder, _metadata

    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. "
                "Run 'python -m src.surrogate.train' first to train the model."
            )
        with open(MODEL_PATH, 'rb') as f:
            _model = pickle.load(f)
        with open(ENCODER_PATH, 'rb') as f:
            _encoder = pickle.load(f)

        import json
        if METADATA_PATH.exists():
            with open(METADATA_PATH, 'r') as f:
                _metadata = json.load(f)

    return _model, _encoder, _metadata


def is_model_trained() -> bool:
    """Check if a trained model exists."""
    return MODEL_PATH.exists() and ENCODER_PATH.exists()


# ============================================================================
# PREDICTION
# ============================================================================

def predict_yield(
    crop_id: str,
    ec_soil: float,
    temperature: float,
    rainfall_mm: float,
) -> dict:
    """
    Predict crop yield and generate all 5 decision-support outputs.

    If the ML model is trained, uses it for relative yield prediction.
    Falls back to Maas-Hoffman formula if model is not available.

    Args:
        crop_id: Crop identifier (e.g., "wheat", "barley", "rice")
        ec_soil: Soil electrical conductivity in dS/m (0–50)
        temperature: Average growing temperature in °C (15–45)
        rainfall_mm: Seasonal rainfall in mm (50–800)

    Returns:
        Dict with all 5 outputs:
        {
            'expected_yield_t_ha': float,
            'relative_yield_pct': float,
            'risk_level': str,
            'recommended_irrigation': str,
            'alternative_halophytes': list,
            'crop_name': str,
            'model_used': str,
            'model_r2': float,
            'confidence': str,
        }
    """
    # --- Input validation ---
    ec_soil = max(0.0, min(50.0, float(ec_soil)))
    temperature = max(15.0, min(45.0, float(temperature)))
    rainfall_mm = max(50.0, min(800.0, float(rainfall_mm)))

    # --- Determine confidence level ---
    confidence = _assess_confidence(ec_soil, temperature, rainfall_mm)

    # --- Try ML model first ---
    ml_relative_yield = None
    model_used = "Maas-Hoffman (formula)"
    model_r2 = None

    if is_model_trained():
        try:
            models_dict, encoder, metadata = _load_model()

            # Per-species model: look up the model for this crop
            if isinstance(models_dict, dict) and crop_id in models_dict:
                species_model = models_dict[crop_id]
                # Features: [ec, ec^2, log(1+ec)] — matches train.py make_features()
                ec_squared = ec_soil ** 2
                ec_log = np.log1p(ec_soil)
                X = np.array([[ec_soil, ec_squared, ec_log]])
                ml_relative_yield = float(species_model.predict(X)[0])
                ml_relative_yield = max(0.0, min(105.0, ml_relative_yield))
                # Get species-specific R2 if available
                if metadata and "species_metrics" in metadata:
                    sp_meta = metadata["species_metrics"].get(crop_id, {})
                    model_r2 = sp_meta.get("r2")
                    model_used = sp_meta.get("model_type", "ML")
                else:
                    model_r2 = metadata.get("test_r2") if metadata else None
                    model_used = metadata.get("model_type", "ML") if metadata else "ML"
            # Fallback: single model (old format)
            elif hasattr(models_dict, 'predict') and crop_id in encoder.classes_:
                species_encoded = encoder.transform([crop_id])[0]
                ec_squared = ec_soil ** 2
                ec_log = np.log1p(ec_soil)
                ec_x_species = ec_soil * species_encoded
                X = np.array([[ec_soil, ec_squared, ec_log, ec_x_species, species_encoded, temperature]])
                ml_relative_yield = float(models_dict.predict(X)[0])
                ml_relative_yield = max(0.0, min(105.0, ml_relative_yield))
                model_r2 = metadata.get("test_r2") if metadata else None
                model_used = metadata.get("model_type", "ML") if metadata else "ML"
        except Exception:
            ml_relative_yield = None

    # --- Generate full prediction (all 5 outputs) ---
    result = full_prediction(
        crop_id=crop_id,
        ec_soil=ec_soil,
        temperature=temperature,
        rainfall_mm=rainfall_mm,
        relative_yield_override=ml_relative_yield,
    )

    # Add metadata
    result['model_used'] = model_used
    result['model_r2'] = model_r2
    result['confidence'] = confidence

    return result


def predict_multiple_crops(
    crop_ids: list,
    ec_soil: float,
    temperature: float,
    rainfall_mm: float,
) -> list:
    """
    Predict yield for multiple crops at the same conditions.
    Useful for the crop comparison view.

    Args:
        crop_ids: List of crop identifiers
        ec_soil: Soil EC in dS/m
        temperature: Temperature in °C
        rainfall_mm: Rainfall in mm

    Returns:
        List of prediction dicts, sorted by relative_yield_pct descending
    """
    results = []
    for crop_id in crop_ids:
        try:
            result = predict_yield(crop_id, ec_soil, temperature, rainfall_mm)
            results.append(result)
        except Exception:
            continue

    # Sort by relative yield (best first)
    results.sort(key=lambda x: x['relative_yield_pct'], reverse=True)
    return results


# ============================================================================
# CONFIDENCE ASSESSMENT
# ============================================================================

def _assess_confidence(ec_soil: float, temperature: float, rainfall_mm: float) -> str:
    """
    Assess prediction confidence based on whether inputs are within
    the range covered by our training data.

    Returns: "high", "medium", or "low"
    """
    # Training data ranges (from our dataset)
    ec_in_range = 0.0 <= ec_soil <= 25.6
    temp_in_range = 25.0 <= temperature <= 35.0
    rain_in_range = 50.0 <= rainfall_mm <= 400.0

    in_range_count = sum([ec_in_range, temp_in_range, rain_in_range])

    if in_range_count == 3:
        return "high"
    elif in_range_count >= 2:
        return "medium"
    else:
        return "low"
