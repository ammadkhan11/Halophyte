"""
Digital Twin for Biosaline Agriculture — Crop Salinity Predictor
================================================================
Interactive web app for predicting crop yield under saline conditions.

Inputs (sidebar sliders + dropdown):
  - Soil EC (dS/m)
  - Temperature (°C)
  - Rainfall (mm)
  - Crop (dropdown)

Outputs (main panel — instant update):
  - Expected Yield (t/ha)
  - Relative Yield (%)
  - Risk Level (Low/Medium/High)
  - Recommended Irrigation
  - Alternative Halophytes

RUN:
    streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.salinity_model.maas_hoffman import (
    get_primary_crops,
    get_crop_params,
    calculate_relative_yield,
)
from src.surrogate.predict import predict_yield, is_model_trained


# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Crop Salinity Predictor — Digital Twin",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
# SIDEBAR — User Inputs (4 inputs as per diagram)
# ============================================================================

st.sidebar.title("🌱 Crop Salinity Predictor")
st.sidebar.markdown("*Digital Twin for Biosaline Agriculture*")
st.sidebar.markdown("---")

# Get available crops (only those with training data)
primary_crops = get_primary_crops()
crop_ids = list(primary_crops.keys())
crop_names = {cid: data['name'] for cid, data in primary_crops.items()}

# INPUT 1: Crop Selection (dropdown)
st.sidebar.header("🌾 Crop")
selected_crop_id = st.sidebar.selectbox(
    "Select crop:",
    options=crop_ids,
    format_func=lambda x: crop_names.get(x, x),
    index=crop_ids.index("wheat") if "wheat" in crop_ids else 0,
)

# INPUT 2: Soil EC (drag-and-drop slider)
st.sidebar.header("💧 Soil Salinity")
ec_soil = st.sidebar.slider(
    "Soil EC (dS/m)",
    min_value=0.0,
    max_value=50.0,
    value=12.0,
    step=0.5,
    help="Electrical Conductivity: 0=fresh, 4=slight, 8=moderate, 15+=very salty"
)

# INPUT 3: Temperature (drag-and-drop slider)
st.sidebar.header("🌡️ Temperature")
temperature = st.sidebar.slider(
    "Average Temperature (°C)",
    min_value=15.0,
    max_value=45.0,
    value=38.0,
    step=1.0,
)

# INPUT 4: Rainfall (drag-and-drop slider)
st.sidebar.header("🌧️ Rainfall")
rainfall_mm = st.sidebar.slider(
    "Seasonal Rainfall (mm)",
    min_value=50.0,
    max_value=800.0,
    value=120.0,
    step=10.0,
)

st.sidebar.markdown("---")

# Model status indicator
if is_model_trained():
    st.sidebar.success("🤖 ML Model: Active")
else:
    st.sidebar.warning("⚠️ ML Model: Not trained — using Maas-Hoffman formula")

st.sidebar.markdown(
    "*Based on 241 data points from 11 Pakistani research papers "
    "(Pakistan Journal of Botany, 2005-2026)*"
)


# ============================================================================
# MAIN CONTENT — Prediction Results
# ============================================================================

st.title("🌱 Digital Twin for Biosaline Agriculture")
st.markdown("### Crop Salinity Predictor — Pakistan")
st.markdown(
    "*Instantly predict crop yield under saline conditions. "
    "All results are estimates based on published Pakistani research data.*"
)

# --- INPUT/OUTPUT SUMMARY BOX (matching the diagram) ---
st.markdown("---")
col_input, col_arrow, col_output = st.columns([2, 1, 3])

with col_input:
    st.markdown("#### 📥 Input")
    st.code(
        f"Soil EC = {ec_soil} dS/m\n"
        f"Temperature = {temperature}°C\n"
        f"Rainfall = {rainfall_mm} mm\n"
        f"Crop = {crop_names[selected_crop_id]}",
        language=None,
    )

# --- PREDICTION (using ML model if available, else Maas-Hoffman) ---
prediction = predict_yield(
    crop_id=selected_crop_id,
    ec_soil=ec_soil,
    temperature=temperature,
    rainfall_mm=rainfall_mm,
)

with col_arrow:
    st.markdown("<br><br><h1 style='text-align:center'>↓</h1>", unsafe_allow_html=True)

with col_output:
    st.markdown("#### 📤 Output")
    alt_names = ", ".join([a['name'] for a in prediction['alternative_halophytes']]) or "None needed"
    st.code(
        f"Expected Yield = {prediction['expected_yield_t_ha']} t/ha\n"
        f"Relative Yield = {prediction['relative_yield_pct']}%\n"
        f"Risk = {prediction['risk_level']}\n"
        f"Recommended Irrigation = {prediction['recommended_irrigation']}\n"
        f"Alternative Halophytes = {alt_names}",
        language=None,
    )

# ============================================================================
# DETAILED METRIC CARDS
# ============================================================================

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "🌾 Expected Yield",
        f"{prediction['expected_yield_t_ha']} t/ha",
        help=f"Based on max potential of {prediction['max_potential_yield_kg_ha']} kg/ha"
    )

with col2:
    st.metric(
        "📊 Relative Yield",
        f"{prediction['relative_yield_pct']}%",
        help="Percentage of maximum possible yield under these conditions"
    )

with col3:
    risk_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
    st.metric(
        "⚠️ Risk Level",
        f"{risk_emoji.get(prediction['risk_level'], '⚪')} {prediction['risk_level']}",
        help="Low: EC < threshold | Medium: declining but viable | High: >50% loss"
    )

col4, col5 = st.columns(2)

with col4:
    st.metric(
        "💧 Recommended Irrigation",
        prediction['recommended_irrigation'],
        help="Based on soil salinity level and available rainfall"
    )

with col5:
    alt_display = ", ".join([a['name'] for a in prediction['alternative_halophytes']]) or "Current crop is optimal"
    st.metric(
        "🌿 Alternative Halophytes",
        alt_display,
        help="Crops with higher salt tolerance that would perform better"
    )


# ============================================================================
# YIELD RESPONSE CURVE
# ============================================================================

st.markdown("---")
st.subheader("📈 Yield vs. Salinity Response Curve")

crop_params = get_crop_params(selected_crop_id)
ec_range = np.arange(0, 50.1, 0.5)

# Use ML model for curve if available, else Maas-Hoffman
curve_yields = []
for ec in ec_range:
    try:
        r = predict_yield(selected_crop_id, float(ec), temperature, rainfall_mm)
        curve_yields.append(r['relative_yield_pct'])
    except Exception:
        curve_yields.append(calculate_relative_yield(float(ec), crop_params['ec_threshold'], crop_params['slope']))

fig = go.Figure()

# Main yield curve
fig.add_trace(go.Scatter(
    x=ec_range, y=curve_yields,
    mode='lines', name=f"{crop_names[selected_crop_id]} yield curve",
    line=dict(color='green', width=3)
))

# Mark current scenario
fig.add_trace(go.Scatter(
    x=[ec_soil], y=[prediction['relative_yield_pct']],
    mode='markers', name='Your scenario',
    marker=dict(color='red', size=14, symbol='star')
))

# Threshold and GR50 lines
fig.add_vline(x=crop_params['ec_threshold'], line_dash="dash", line_color="orange",
              annotation_text=f"Threshold ({crop_params['ec_threshold']} dS/m)")
fig.add_vline(x=crop_params['gr50'], line_dash="dash", line_color="red",
              annotation_text=f"GR50 ({crop_params['gr50']} dS/m)")

fig.update_layout(
    xaxis_title="Soil Salinity (EC, dS/m)",
    yaxis_title="Relative Yield (%)",
    yaxis_range=[0, 110],
    height=400,
    legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
)
st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# ALTERNATIVE CROPS TABLE
# ============================================================================

if prediction['alternative_halophytes']:
    st.subheader("🌿 Recommended Alternative Crops")
    st.markdown(f"*These crops have higher salt tolerance and would perform better at EC = {ec_soil} dS/m:*")

    alt_data = []
    for alt in prediction['alternative_halophytes']:
        alt_data.append({
            "Crop": alt['name'],
            "Scientific Name": alt['scientific_name'],
            "EC Threshold (dS/m)": alt['ec_threshold'],
            "GR50 (dS/m)": alt['gr50'],
            "Notes": alt['note'],
        })

    st.dataframe(pd.DataFrame(alt_data), use_container_width=True, hide_index=True)
else:
    st.success("✅ Your selected crop is well-suited for these conditions! No alternatives needed.")


# ============================================================================
# MODEL INFO & DATA SOURCES
# ============================================================================

st.markdown("---")
col_model, col_source = st.columns(2)

with col_model:
    st.subheader("🤖 Model Information")
    model_r2 = prediction.get('model_r2')
    model_used = prediction.get('model_used', 'Maas-Hoffman')
    confidence = prediction.get('confidence', 'medium')

    conf_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}
    st.markdown(f"""
    - **Algorithm:** {model_used}
    - **R² Score:** {f'{model_r2:.4f}' if model_r2 else 'N/A (formula-based)'}
    - **Confidence:** {conf_emoji.get(confidence, '⚪')} {confidence.upper()}
    - **Training data:** 241 points from 11 Pakistani papers
    """)

with col_source:
    st.subheader("📚 Data Source")
    st.markdown(f"""
    - **Crop:** {crop_params.get('name')} (*{crop_params.get('scientific_name')}*)
    - **Source:** {crop_params.get('source', 'FAO Paper 29')}
    - **Dataset points:** {crop_params.get('dataset_points', 0)}
    - **EC range tested:** {crop_params.get('ec_range_tested', 'N/A')} dS/m
    """)


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    "*Digital Twin for Biosaline Agriculture — Crop Salinity Predictor | "
    "FYP Project — Group 15, Section B | "
    "Data: 241 points from 11 Pakistani papers (Pak. J. Bot., 2005-2026)*"
)
