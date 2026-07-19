"""
Salinity Model Module
=====================
Maas-Hoffman salinity response model + risk assessment + irrigation
recommendations + alternative crop suggestions.

Trained on 241 data points from 11 Pakistani research papers.
"""

from .maas_hoffman import (
    calculate_relative_yield,
    get_crop_params,
    get_all_crops,
    get_primary_crops,
    assess_risk_level,
    recommend_irrigation,
    suggest_alternatives,
    full_prediction,
)
