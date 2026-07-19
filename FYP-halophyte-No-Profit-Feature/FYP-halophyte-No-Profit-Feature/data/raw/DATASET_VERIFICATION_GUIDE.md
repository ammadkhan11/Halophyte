# 📋 Dataset Verification Guide
## How to Verify AuthenticHalophyteData.xlsx (v3.0 — 241 Data Points)

---

## 📊 DATASET SUMMARY

| Metric | Value |
|--------|-------|
| **Total data points** | 241 |
| **Species covered** | 6 (barley, maize, quinoa, rice, sorghum, wheat) |
| **Unique varieties/genotypes** | 67 |
| **Salinity range** | 0 – 50 dS/m |
| **Source papers** | 11 Pakistani research papers |
| **All data from** | Pakistan (Punjab, Sindh, KPK) |

### Data Points Per Species:
| Species | Points | Varieties | EC Range |
|---------|--------|-----------|----------|
| Barley | 54 | 15 genotypes | 0–15 dS/m |
| Wheat | 53 | 19 genotypes | 1.5–15 dS/m |
| Maize | 40 | 10 hybrids | 0–12 dS/m |
| Sorghum | 40 | 8 varieties | 0–25.6 dS/m |
| Rice | 36 | 12 genotypes | 0–7.5 dS/m |
| Quinoa | 18 | 3 varieties | 0–50 dS/m |

---

## 🔍 STEP-BY-STEP VERIFICATION PROCESS

### Step 1: Open the Excel File
Open `d:\masood\FYP\data\raw\AuthenticHalophyteData.xlsx`

### Step 2: Check Column Structure
The file should have these 11 columns:
1. `species_id` — e.g., "wheat", "rice", "barley"
2. `scientific_name` — Full Latin name
3. `variety` — Specific cultivar/genotype tested
4. `ec_soil_dS_m` — Salinity level in dS/m
5. `growth_measure` — What was measured
6. `relative_yield_pct` — Growth as % of control (0–100+)
7. `temperature_C` — Growing temperature (may be blank)
8. `location` — Where in Pakistan the experiment was done
9. `source_file` — PDF filename from your collection
10. `source_reference` — Full citation
11. `notes` — Additional context

### Step 3: Verify Against Source Papers (Spot Check)

Pick ANY row and verify it against the original paper. Here's how:

---

## 📄 SOURCE-BY-SOURCE VERIFICATION

### Source 1: Gul et al., 2026 — Quinoa
- **File:** `1111.pdf`
- **Citation:** Gul et al., 2026. Pak. J. Bot. 58(2)
- **What to check:** Paper states quinoa shoot fresh weight reduced by 86.1% (Q-1), 71.5% (Q-2), 66.8% (Q-3) at 500 mM NaCl
- **In Excel:** Look for rows with species="quinoa", ec=50, variety="UAF-Q7 (Q-1)" → relative_yield should be 13.9% (100 - 86.1)
- **Page/Section:** Results section, paragraph about "fresh weight reductions"

### Source 2: Akram et al., 2010 — Maize
- **File:** `1769756278.pdf`
- **Citation:** Akram et al., 2010. Pak. J. Bot. 42(1):141-154
- **What to check:** Table 3 shows plant fresh weight for 10 hybrids at 0, 40, 80, 120 mM NaCl
- **In Excel:** Look for species="maize", variety="Pioneer32B33", ec=0 → relative_yield=100%
- **Verification:** Pioneer32B33 control=4.54g, at 120mM=3.55g → 3.55/4.54×100 = 78.2%
- **Page/Section:** Table 3

### Source 3: Hameed et al., 2008 — Wheat (seedling)
- **File:** `PJB40(3)1043.pdf`
- **Citation:** Hameed et al., 2008. Pak. J. Bot. 40(3):1043-1051
- **What to check:** Figure 1 shows seedling fresh weight for Lu-26 and Pak-81
- **In Excel:** species="wheat", variety="Lu-26 (salt tolerant)", ec=15 → ~63.6%
- **Page/Section:** Figure 1

### Source 4: Shafi et al., 2013 — Wheat (field yield)
- **File:** `10.pdf`
- **Citation:** Shafi et al., 2013. Pak. J. Bot. 45(3):787-794
- **What to check:** Table 8 has grain yield (kg/ha) at 3 field sites with different EC
- **In Excel:** species="wheat", variety="SR-40", ec=3.25 → relative_yield=100% (reference site)
- **Cross-check:** SR-40 at Baboo Dehari (EC 4.25): 2360/2536.67×100 = 93.0%
- **Page/Section:** Table 8

### Source 5: Shereen et al., 2022 — Rice
- **File:** `1646201855.pdf`
- **Citation:** Shereen et al., 2022. Pak. J. Bot. 54(3):787-794
- **What to check:** Table 3 has shoot fresh weight (mg) at 0, 50, 75 mM NaCl
- **In Excel:** species="rice", variety="FL-478 (tolerant check)", ec=5 → 356.4/367.2×100 = 97.1%
- **Page/Section:** Table 3

### Source 6: Shereen et al., 2005 — Rice
- **File:** `PJB37(1)131.pdf`
- **Citation:** Shereen et al., 2005. Pak. J. Bot. 37(1):131-139
- **What to check:** Figures 1 & 2 show % fresh weight at 75 mM for various lines
- **In Excel:** species="rice", variety="L-96 (tolerant)", ec=7.5 → 93%
- **Page/Section:** Figure 2

### Source 7: Khan et al., 2009 — Wheat (grain yield)
- **File:** `1768369841.pdf`
- **Citation:** Khan et al., 2009. Pak. J. Bot. 41(2):633-638
- **What to check:** Table 2 has grain yield at EC 1.5 and 12 dS/m
- **In Excel:** species="wheat", variety="Lu-26s", ec=12 → 2728/3503×100 = 77.9%
- **Page/Section:** Table 2

### Source 8: Kausar et al., 2012 — Sorghum
- **File:** `07 (1).pdf`
- **Citation:** Kausar et al., 2012. Pak. J. Bot. 44(1):47-52
- **What to check:** Table 4 has Shoot Fresh Weight Stress Index (SFSI = % of control)
- **In Excel:** species="sorghum", variety="JS-2002 (tolerant)", ec=10 → 71.7%
- **Page/Section:** Table 4

### Source 9: Anwar et al., 2011 — Barley
- **File:** `07.pdf`
- **Citation:** Anwar et al., 2011. Pak. J. Bot. 43(6):2687-2691
- **What to check:** Table 1 has shoot fresh weight (g/plant) at 0, 50, 100, 150 mM NaCl
- **In Excel:** species="barley", variety="Balochistan-Local (tolerant)", ec=5 → 8.82/10.15×100 = 86.9%
- **Page/Section:** Table 1

### Source 10: Hussain et al., 2024 — Sorghum
- **File:** `1710928021.pdf`
- **Citation:** Hussain et al., 2024. Pak. J. Bot. 56(3):807-814
- **What to check:** Table 6 has fresh weight at 0, 2.5, 5, 10, 15 g/L NaCl
- **In Excel:** species="sorghum", variety="Local (D.I. Khan)", ec=8.5 → 83.92/105.62×100 = 79.5%
- **Page/Section:** Table 6

### Source 11: Mahmood, 2011 — Barley
- **File:** `PJB43(3)1651.pdf`
- **Citation:** Mahmood, 2011. Pak. J. Bot. 43(3):1651-1654
- **What to check:** Table 1 has shoot dry mass (g/pot) at 0 and 100 mM NaCl
- **In Excel:** species="barley", variety="PK-30130 (tolerant, EC50=18.4)", ec=12 → 3.43/4.65×100 = 73.8%
- **Page/Section:** Table 1

---

## ✅ VERIFICATION CHECKLIST

Use this checklist when verifying:

- [ ] Excel file opens correctly with 241 rows of data
- [ ] All 11 columns are present and properly named
- [ ] Spot-check 3 random rows against their source papers
- [ ] Control values (ec=0) all show relative_yield = 100%
- [ ] All relative_yield values are between 0 and 105 (quinoa can exceed 100 due to halophyte behavior)
- [ ] EC values make sense (converted correctly from mM NaCl or g/L)
- [ ] Each source_file matches a PDF you actually have
- [ ] Locations are all in Pakistan
- [ ] No duplicate rows

---

## 🔢 UNIT CONVERSION VERIFICATION

| Paper Reports | Conversion Used | Verify With |
|---------------|-----------------|-------------|
| mM NaCl | ÷10 = dS/m (approx) | 100 mM ≈ 10 dS/m |
| g/L NaCl | ×1.71 = dS/m (approx) | 5 g/L ≈ 8.5 dS/m |
| % seawater | ×0.5 = dS/m | 100% SW ≈ 50 dS/m |

**Important:** These are standard approximate conversions used in salinity research. Exact conversion depends on temperature and solution composition.

---

## 🧪 QUICK SANITY CHECKS

### Do the trends make sense biologically?
1. **Higher EC → Lower relative yield** (should decrease for all crops except quinoa at low EC)
2. **Tolerant varieties → Higher relative yield at same EC** than sensitive varieties
3. **Rice** should be most sensitive (low EC tolerance threshold)
4. **Barley** should be most tolerant among conventional crops
5. **Quinoa** can show slight INCREASE at low EC (halophyte behavior, 100-105%)

### Expected tolerance ranking (from our data):
```
Most tolerant ←――――――――――――――――――――→ Most sensitive
Quinoa > Sorghum > Barley > Wheat > Maize > Rice
```

---

## 📁 FILES IN THIS DATASET PACKAGE

| File | Purpose |
|------|---------|
| `AuthenticHalophyteData.xlsx` | The main dataset (241 rows) |
| `create_authentic_dataset.py` | Script that generates the Excel (for reproducibility) |
| `DATASET_VERIFICATION_GUIDE.md` | This file |

---

## 🚀 HOW TO REGENERATE THE DATASET

If you need to regenerate the Excel file (e.g., after corrections):

```bash
cd d:\masood\FYP
python data\raw\create_authentic_dataset.py
```

This will overwrite `AuthenticHalophyteData.xlsx` with fresh data from all 11 sources.

---

*Dataset Version: 3.0*  
*Last Generated: July 2026*  
*Total Sources: 11 Pakistani research papers (all from Pakistan Journal of Botany)*
