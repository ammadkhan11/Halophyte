# Halophyte Grass Dictionary and ML-Based Salt Tolerance Prediction System

## Project Overview

This final year project is a web-based halophyte grass dictionary with an ML-supported prediction module for salt tolerance and ion concentration factors.

## Phase 1: Grass Dictionary

Phase 1 provides a searchable and filterable grass library. Users can browse grass species, compare mechanisms, inspect GR50 ranges, view ion concentration values, sort records, open detailed profiles, and use a unit conversion helper.

## Phase 2: Prediction Model

Phase 2 estimates missing numeric salt tolerance and ion concentration values. The prediction module supports grass-based and mechanism-based prediction modes.

## Dataset Fields

Important fields include species, common name, mechanism, GR50 minimum, GR50 maximum, GR50 average, Na+ shoot/root, Cl- shoot/root, K+ shoot/root, salt tolerance level, and ion category fields.

## Prediction Methods

Each grass has one available record, so separate per-species models are not statistically valid. The system therefore uses species-anchored regression for grass-based prediction and KNN weighted estimation for mechanism-based prediction.

## Why Individual Per-Grass Models Are Not Used

A separate model for one grass would require multiple observations for that species. Since each species has only one row, a per-grass model would not be statistically meaningful.

## Grass-Based Prediction Explanation

Grass-based prediction uses the selected species as the base profile. The entered known value is compared with the stored dataset value. The difference is used to adjust remaining fields using regression patterns learned from the dataset.

## Mechanism-Based Prediction Explanation

Mechanism-based prediction uses the selected mechanism group, such as Salt-Secreting or Non-Secreting. It finds nearest records based on the entered known value and calculates weighted estimates for the remaining numeric fields.

## Current Limitations

The dataset contains 30 grass records, so predictions are estimates and should not be interpreted as final biological measurements. The model is intended for academic learning, comparison, and demonstration of ML-assisted estimation.

## Future Improvements

Future work could include a larger dataset, more observations per species, stronger validation, uncertainty intervals, and integration of additional environmental or experimental variables.
