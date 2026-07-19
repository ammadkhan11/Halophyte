"""
Salinity Model — Maas-Hoffman + Risk + Irrigation + Alternatives
================================================================
Core decision-support logic for the Digital Twin.

Provides:
- Maas-Hoffman relative yield calculation
- Risk level assessment (Low/Medium/High)
- Irrigation recommendation
- Alternative crop suggestions
"""

from pathlib import Path
from typing import Optional
import yaml


# ============================================================================
# CONFIG LOADING
# ============================================================================

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "crops.yaml"
_CROPS_CACHE: Optional[dict] = None


def _load_crops_config() -> dict:
    """Load crops configuration from YAML file."""
    global _CROPS_CACHE
    if _CROPS_CACHE is None:
        with open(_CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        _CROPS_CACHE = config.get('crops', {})
    return _CROPS_CACHE


def get_all_crops() -> dict:
    """Get all crops from config."""
    return _load_crops_config()


def get_primary_crops() -> dict:
    """Get only crops that are in our training dataset (dataset_points > 0)."""
    crops = _load_crops_config()
    return {k: v for k, v in crops.items() if v.get('dataset_points', 0) > 0}


def get_crop_params(crop_id: str) -> dict:
    """Get parameters for a specific crop."""
    crops = _load_crops_config()
    if crop_id not in crops:
        raise ValueError(f"Unknown crop: '{crop_id}'. Available: {list(crops.keys())}")
    return crops[crop_id]


# ============================================================================
# MAAS-HOFFMAN MODEL
# ============================================================================

def calculate_relative_yield(ec_soil: float, ec_threshold: float, slope: float) -> float:
    """
    Calculate relative yield using the Maas-Hoffman linear model.
    
    Args:
        ec_soil: Soil electrical conductivity (dS/m)
        ec_threshold: Crop-specific salinity threshold (dS/m)
        slope: Yield decline rate (%/(dS/m))
    
    Returns:
        Relative yield as percentage (0–100)
    """
    if ec_soil < 0:
        raise ValueError(f"EC cannot be negative, got {ec_soil}")
    
    if ec_soil <= ec_threshold:
        return 100.0
    
    relative_yield = 100.0 - slope * (ec_soil - ec_threshold)
    return max(0.0, min(100.0, relative_yield))


# ============================================================================
# RISK LEVEL ASSESSMENT
# ============================================================================

def assess_risk_level(ec_soil: float, crop_id: str) -> str:
    """
    Assess risk level based on how close EC is to crop's tolerance limit.
    
    Risk levels:
    - Low: EC < crop's ec_threshold (yield barely affected)
    - Medium: EC between threshold and GR50 (yield declining but viable)
    - High: EC > crop's GR50 (more than 50% yield loss expected)
    
    Args:
        ec_soil: Soil EC in dS/m
        crop_id: Crop identifier from config
    
    Returns:
        "Low", "Medium", or "High"
    """
    params = get_crop_params(crop_id)
    ec_threshold = params['ec_threshold']
    gr50 = params['gr50']
    
    if ec_soil <= ec_threshold:
        return "Low"
    elif ec_soil <= gr50:
        return "Medium"
    else:
        return "High"


# ============================================================================
# IRRIGATION RECOMMENDATION
# ============================================================================

def recommend_irrigation(ec_soil: float, rainfall_mm: float) -> str:
    """
    Recommend irrigation frequency based on salinity and rainfall.
    
    Logic:
    - If rainfall > 400mm AND EC < 5: "Minimal supplemental irrigation"
    - If rainfall 200-400mm OR EC 5-10: "Weekly irrigation"
    - If rainfall < 200mm OR EC 10-20: "Twice weekly irrigation"
    - If EC > 20: "Daily drip irrigation with leaching fraction"
    
    Args:
        ec_soil: Soil EC in dS/m
        rainfall_mm: Seasonal rainfall in mm
    
    Returns:
        Irrigation recommendation string
    """
    # Highest priority: very high salinity always needs daily drip
    if ec_soil > 20:
        return "Daily drip irrigation with leaching fraction"
    
    # Low salinity + good rainfall
    if rainfall_mm > 400 and ec_soil < 5:
        return "Minimal supplemental irrigation"
    
    # Moderate conditions
    if ec_soil >= 10 or rainfall_mm < 200:
        return "Twice weekly irrigation"
    
    # Default: moderate salinity or moderate rainfall
    return "Weekly irrigation"


# ============================================================================
# ALTERNATIVE CROP SUGGESTIONS
# ============================================================================

def suggest_alternatives(ec_soil: float, current_crop_id: str, top_n: int = 3) -> list:
    """
    Suggest alternative crops that would perform better at this salinity.
    
    Logic:
    - Find all crops in config where ec_threshold > current EC
    - Sort by tolerance (highest GR50 first)
    - Return top N alternatives (excluding the current crop)
    
    Args:
        ec_soil: Current soil EC in dS/m
        current_crop_id: The crop the user currently selected
        top_n: Number of alternatives to suggest (default 3)
    
    Returns:
        List of dicts with {crop_id, name, gr50, ec_threshold, note}
    """
    crops = _load_crops_config()
    
    alternatives = []
    for crop_id, params in crops.items():
        # Skip current crop
        if crop_id == current_crop_id:
            continue
        
        # Only suggest crops that would perform better at this EC
        if params.get('ec_threshold', 0) > ec_soil:
            alternatives.append({
                'crop_id': crop_id,
                'name': params.get('name', crop_id),
                'scientific_name': params.get('scientific_name', ''),
                'gr50': params.get('gr50', 0),
                'ec_threshold': params.get('ec_threshold', 0),
                'note': params.get('note', ''),
            })
    
    # Sort by GR50 (highest tolerance first)
    alternatives.sort(key=lambda x: x['gr50'], reverse=True)
    
    return alternatives[:top_n]


# ============================================================================
# FULL PREDICTION (ALL 5 OUTPUTS)
# ============================================================================

def full_prediction(
    crop_id: str,
    ec_soil: float,
    temperature: float,
    rainfall_mm: float,
    relative_yield_override: Optional[float] = None,
) -> dict:
    """
    Generate a complete prediction with all 5 output pillars.
    
    If relative_yield_override is provided (from ML model), use that.
    Otherwise, calculate using Maas-Hoffman formula.
    
    Args:
        crop_id: Crop identifier
        ec_soil: Soil EC in dS/m
        temperature: Temperature in °C
        rainfall_mm: Seasonal rainfall in mm
        relative_yield_override: ML model prediction (optional)
    
    Returns:
        Dict with: expected_yield_t_ha, relative_yield_pct, risk_level,
                   recommended_irrigation, alternative_halophytes
    """
    params = get_crop_params(crop_id)
    
    # 1. Relative Yield
    if relative_yield_override is not None:
        relative_yield = relative_yield_override
    else:
        relative_yield = calculate_relative_yield(
            ec_soil, params['ec_threshold'], params['slope']
        )
    
    # 2. Expected Yield (t/ha)
    max_yield_kg = params.get('max_potential_yield', 5000)
    expected_yield_kg = (relative_yield / 100.0) * max_yield_kg
    expected_yield_t_ha = expected_yield_kg / 1000.0
    
    # 3. Risk Level
    risk_level = assess_risk_level(ec_soil, crop_id)
    
    # 4. Irrigation Recommendation
    irrigation = recommend_irrigation(ec_soil, rainfall_mm)
    
    # 5. Alternative Halophytes
    alternatives = suggest_alternatives(ec_soil, crop_id)
    
    return {
        'expected_yield_t_ha': round(expected_yield_t_ha, 2),
        'relative_yield_pct': round(relative_yield, 1),
        'risk_level': risk_level,
        'recommended_irrigation': irrigation,
        'alternative_halophytes': alternatives,
        'crop_name': params.get('name', crop_id),
        'max_potential_yield_kg_ha': max_yield_kg,
    }
