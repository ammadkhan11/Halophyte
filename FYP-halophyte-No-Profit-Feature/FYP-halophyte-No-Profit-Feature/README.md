# 🌱 Digital Twin for Biosaline Agriculture
## Crop Salinity Predictor — Pakistan

A decision-support tool that predicts crop yield under saline conditions using published Pakistani research data.

### What It Does

Given 4 simple inputs:
- **Soil EC** (dS/m) — How salty is the soil?
- **Temperature** (°C) — Average growing temperature
- **Rainfall** (mm) — Seasonal rainfall
- **Crop** — Which crop to grow

It produces 5 outputs:
- **Expected Yield** (t/ha) — Estimated production
- **Relative Yield** (%) — Percentage of maximum potential
- **Risk Level** — Low / Medium / High
- **Recommended Irrigation** — Frequency suggestion
- **Alternative Halophytes** — Better-suited crops if conditions are harsh

---

### Dataset

- **241 data points** from **11 Pakistani research papers** (Pakistan Journal of Botany, 2005-2026)
- **6 crops**: Barley, Wheat, Maize, Sorghum, Rice, Quinoa
- **67 varieties/genotypes** tested at various salinity levels
- All data from Pakistani institutions (NIAB Faisalabad, NIA Tandojam, KPK Ag. Univ., etc.)

---

### Integrated Local App

```bash
# From the main project root
npm.cmd run dev:all
```

Open:

```text
http://127.0.0.1:5173/crop-salinity-screening
```

The final local app route is the main React/FastAPI integration, not Streamlit. The original
`app/streamlit_app.py` remains as source/provenance for the converted interface.

To train the optional surrogate model files when the dataset and dependencies are ready:

```bash
python -m src.surrogate.train
```

---

### Project Structure

```
FYP/
├── AGENTS.md                    # Project rules & guidelines
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── config/
│   ├── crops.yaml               # Crop parameters (Maas-Hoffman)
│   └── simulation.yaml          # ML model configuration
├── data/
│   └── raw/
│       ├── AuthenticHalophyteData.xlsx    # Training dataset (241 points)
│       ├── create_authentic_dataset.py     # Script to regenerate Excel
│       └── DATASET_VERIFICATION_GUIDE.md   # How to verify data
├── src/
│   ├── salinity_model/
│   │   └── maas_hoffman.py      # Core model + risk + irrigation + alternatives
│   └── surrogate/
│       ├── train.py             # ML model training
│       └── predict.py           # ML model inference
├── app/
│   └── streamlit_app.py         # Interactive web app
├── models/                      # Saved trained ML models
├── notebooks/                   # Jupyter exploration
└── tests/                       # Unit tests
```

---

### Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| ML Model | Gradient Boosting (scikit-learn) |
| Web App | Streamlit |
| Visualization | Plotly |
| Data | pandas + openpyxl |

---

### Team

FYP Project — Group 15, Section B  
University of Karachi, Department of Computer Science

---

*All predictions are estimates based on published Pakistani research. Not a replacement for expert agricultural advice.*
