# AGENTS.md — Project Rules, Boundaries & Coding Guidelines
## Digital Twin for Biosaline Agriculture — Crop Salinity Predictor

---

## 🎯 PROJECT IDENTITY — What We Are Building

We are building a **decision-support tool** (a "digital twin") that helps farmers and agricultural advisors answer:
> "If I grow crop X in soil with salinity Y, what yield can I expect and what are my alternatives?"

**System Input/Output (as shown in the diagram):**

```
Input (sidebar — drag-and-drop sliders + dropdown):
  Soil EC = 12 dS/m          ← slider (0–50 dS/m)
  Temperature = 38°C         ← slider (15–45°C)
  Rainfall = 120 mm          ← slider (50–800 mm)
  Crop = Panicum antidotale  ← dropdown selector
        ↓
Output (main panel — instant update):
  Expected Yield = 18.4 t/ha
  Relative Yield = 82%
  Risk = Medium
  Recommended Irrigation = Weekly
  Alternative Halophytes = Atriplex, Kochia
```

**UI Style:** Streamlit sidebar with interactive sliders (user drags to set values)
and a dropdown for crop selection. Results update instantly on the main panel.

**We are building a LAYER ON TOP of existing science** that combines:
1. A fast ML surrogate model (trained on Pakistani research data)
2. Risk assessment based on salinity tolerance thresholds
3. Irrigation recommendations based on crop-salinity-climate interactions
4. Alternative crop suggestions when conditions are suboptimal
5. An interactive web app (for non-experts to test scenarios)

---

## 🚫 DIFFERENTIATION RULES — What Makes Us Different from Existing Tools

### Rule 1: We Do NOT Rebuild DSSAT/APSIM
- We use **published Pakistani research data** as our training source
- Our ML model learns salinity-yield relationships from 11 Pakistani papers (241 data points)
- We do NOT replicate crop simulation engine internals

### Rule 2: Our Unique Value is SPEED + RECOMMENDATIONS + ACCESSIBILITY
| Existing Tools (AquaCrop/DSSAT/SALTMED) | Our Project |
|---|---|
| Requires expert setup & calibration | Simple web UI anyone can use |
| Minutes per simulation | Milliseconds (ML surrogate) |
| Outputs only raw yield | Outputs **yield + risk + irrigation + alternatives** |
| No halophyte focus | Pakistan-specific halophyte data |
| No alternative crop suggestions | Recommends better-suited crops |
| Complex parameter tuning | Just 4 inputs needed |

### Rule 3: Our Five Output Pillars
Every prediction must provide ALL of these:
1. **Expected Yield (t/ha)** — Absolute yield estimate
2. **Relative Yield (%)** — Percentage of maximum potential yield
3. **Risk Level** — Low/Medium/High based on salinity vs. crop tolerance
4. **Recommended Irrigation** — Frequency suggestion based on conditions
5. **Alternative Halophytes** — Better-suited crops if current one is at risk

### Rule 4: Results Must Be Verifiable
- Show WHERE each number comes from (cite the source paper)
- Show the confidence level
- Provide reference data for comparison
- Never present results as absolute truth — always as "estimates based on published Pakistani research"

---

## 📋 PROJECT SCOPE — What's In and What's Out

### ✅ IN SCOPE
- ML surrogate model trained on **Pakistani salinity-yield research data** (241 data points from 11 papers)
- Yield prediction (t/ha and relative %)
- Risk level classification (Low/Medium/High)
- Irrigation frequency recommendation
- Alternative halophyte crop suggestions
- Streamlit interactive web app
- Input validation with warnings when outside trained range
- Maas-Hoffman salinity response model as baseline

### ❌ OUT OF SCOPE
- ~~Profit/cost/revenue calculations~~ (REMOVED)
- ~~Monte Carlo economic simulations~~ (REMOVED)
- ~~Breakeven salinity calculator~~ (REMOVED)
- ~~Market price tracking~~ (REMOVED)
- Building a new crop simulation engine
- Real-time IoT sensor integration
- Mobile app development
- User authentication / multi-tenancy

---

## 🌱 DOMAIN KNOWLEDGE — Key Concepts

### What is EC (Electrical Conductivity)?
The standard unit for measuring water/soil salinity. Measured in dS/m.
- Freshwater: < 0.7 dS/m
- Slightly saline: 0.7–3 dS/m  
- Moderately saline: 3–6 dS/m
- Highly saline: 6–14 dS/m
- Very highly saline: > 14 dS/m

### What is the Maas-Hoffman Model?
`Yr = 100 - s × (ECe - ECt)` where:
- Yr = relative yield %
- ECe = soil salinity
- ECt = threshold (crop-specific)
- s = slope (crop-specific decline rate)

### Target Crops (From Our Pakistani Dataset)
| Species | Dataset Points | EC Range Tested |
|---------|---------------|-----------------|
| Barley (Hordeum vulgare) | 54 | 0–15 dS/m |
| Wheat (Triticum aestivum) | 53 | 0–15 dS/m |
| Maize (Zea mays) | 40 | 0–12 dS/m |
| Sorghum (Sorghum bicolor) | 40 | 0–25.6 dS/m |
| Rice (Oryza sativa) | 36 | 0–7.5 dS/m |
| Quinoa (Chenopodium quinoa) | 18 | 0–50 dS/m |

### Additional Crops in Config (from literature, for recommendations)
- Panicum antidotale (Blue Panicgrass)
- Rhodes Grass, Bermudagrass, Seashore Paspalum
- Salicornia, and 19 ecological/research grasses

---

## 💻 CODE PRACTICES

### Project Structure
```
FYP/
├── AGENTS.md                    # This file
├── README.md                    # Setup & run instructions
├── requirements.txt             # Python dependencies
├── config/
│   ├── crops.yaml               # Crop parameters (Maas-Hoffman + alternatives)
│   └── simulation.yaml          # ML model & prediction parameters
├── data/
│   ├── raw/                     # AuthenticHalophyteData.xlsx + generation script
│   └── processed/               # ML-ready training data
├── src/
│   ├── __init__.py
│   ├── salinity_model/          # Maas-Hoffman + risk + irrigation logic
│   │   ├── __init__.py
│   │   └── maas_hoffman.py
│   └── surrogate/               # ML surrogate model (training, inference)
│       ├── __init__.py
│       ├── train.py
│       └── predict.py
├── app/
│   └── streamlit_app.py         # Interactive web app
├── notebooks/                   # Jupyter notebooks for exploration
├── tests/                       # Unit tests
│   ├── test_salinity_model.py
│   └── test_surrogate.py
└── models/                      # Saved trained ML models (.pkl)
```

### General Principles
1. **Python 3.10+** is the project language
2. **Keep it simple** — readability over cleverness
3. **Document everything** — docstrings on all functions
4. **Type hints everywhere**
5. **No magic numbers** — all constants in config files

### Dependencies — Keep Minimal
- `numpy`, `pandas` — data handling
- `scikit-learn` — ML surrogate model
- `streamlit` — web app
- `pyyaml` — config loading
- `plotly` — visualization
- `openpyxl` — Excel file reading

---

## 📊 MODEL OUTPUTS — What the System Must Produce

### For every prediction, output these 5 values:

| Output | How Calculated |
|--------|---------------|
| **Expected Yield (t/ha)** | `relative_yield% × max_potential_yield / 1000` |
| **Relative Yield (%)** | ML model prediction (trained on Pakistani data) |
| **Risk Level** | Based on how close EC is to crop's tolerance limit |
| **Recommended Irrigation** | Based on EC level + rainfall + crop water needs |
| **Alternative Halophytes** | Crops with higher tolerance at this EC level |

### Risk Level Logic:
- **Low**: EC < crop's ec_threshold (yield barely affected)
- **Medium**: EC between threshold and GR50 (yield declining but viable)
- **High**: EC > crop's GR50 (more than 50% yield loss expected)

### Irrigation Recommendation Logic:
- If rainfall > 400mm AND EC < 5: "Minimal supplemental"
- If rainfall 200-400mm OR EC 5-10: "Weekly"
- If rainfall < 200mm OR EC 10-20: "Twice weekly"
- If EC > 20: "Daily drip irrigation with leaching"

### Alternative Halophytes Logic:
- Find all crops in config where `ec_threshold > current_EC`
- Sort by tolerance (highest GR50 first)
- Return top 3 alternative crops that would perform better

---

## 📊 KEY METRICS

| Metric | Target |
|---|---|
| ML model R² on test data | > 0.85 (real data is noisy) |
| Prediction latency | < 100ms |
| App load time | < 3 seconds |
| Crops supported | 6 (from dataset) + alternatives from config |
| Outputs per prediction | 5 (yield, relative%, risk, irrigation, alternatives) |
| Valid salinity input range | 0–50 dS/m |

---

## 🔄 WORKFLOW

### Phase Priority Order
1. **Phase 1: Data Preparation** ✅ — Pakistani dataset collected (241 points, 11 papers)
2. **Phase 2: ML Model Training** — Train surrogate on AuthenticHalophyteData.xlsx
3. **Phase 3: Prediction Engine** — Build predict function with all 5 outputs
4. **Phase 4: Web App** — Streamlit dashboard matching the diagram
5. **Phase 5: Validation** — Test against held-out data, verify against source papers

---

## 🛑 STOP AND ASK — When to Pause

Stop and ask the human for guidance when:
- Model accuracy is below R² = 0.80
- Adding a new dependency not listed here
- The 241 data points seem insufficient for a particular crop
- Architectural decisions that affect multiple modules

---

*Last updated: July 2026*
*Project: FYP — Digital Twin for Biosaline Agriculture (Crop Salinity Predictor)*
*Data: 241 data points from 11 Pakistani research papers (Pakistan Journal of Botany)*
