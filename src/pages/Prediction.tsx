import { useEffect, useMemo, useState } from 'react';
import { Activity, AlertCircle, Loader2, Sprout } from 'lucide-react';
import {
  getGrassOptions,
  getPredictionMetadata,
  predictValues,
  type GrassOption,
  type PredictionMode,
  type PredictionResponse,
} from '../lib/predictionApi';

const FIELD_LABELS: Record<string, string> = {
  gr50_avg: 'GR50 Average (dS/m)',
  na_shoot: 'Na+ Shoot (mmol kg-1 Tissue DW)',
  na_root: 'Na+ Root (mmol kg-1 Tissue DW)',
  cl_shoot: 'Cl- Shoot (mmol kg-1 Tissue DW)',
  cl_root: 'Cl- Root (mmol kg-1 Tissue DW)',
  k_shoot: 'K+ Shoot (mmol kg-1 Tissue DW)',
  k_root: 'K+ Root (mmol kg-1 Tissue DW)',
};

const DEFAULT_FIELDS = Object.keys(FIELD_LABELS);
const DEFAULT_MECHANISMS = ['Non-Secreting', 'Salt-Secreting'];

function formatPredictionValue(field: string, value: number) {
  const suffix = field === 'gr50_avg' ? ' dS/m' : ' mmol kg-1 Tissue DW';
  return `${Number(value).toFixed(2)}${suffix}`;
}

function formatFieldLabel(field: string) {
  return FIELD_LABELS[field] ?? field;
}

function PredictionGroup({
  title,
  fields,
  predictions,
}: {
  title: string;
  fields: string[];
  predictions: Record<string, number>;
}) {
  const visibleFields = fields.filter((field) => predictions[field] !== undefined);

  if (visibleFields.length === 0) {
    return null;
  }

  return (
    <section className="prediction-result-group">
      <h3>{title}</h3>
      <dl>
        {visibleFields.map((field) => (
          <div key={field}>
            <dt>{formatFieldLabel(field)}</dt>
            <dd>{formatPredictionValue(field, predictions[field])}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export default function Prediction() {
  const [mode, setMode] = useState<PredictionMode>('grass_based');
  const [species, setSpecies] = useState('');
  const [mechanism, setMechanism] = useState('');
  const [knownField, setKnownField] = useState('gr50_avg');
  const [knownValue, setKnownValue] = useState('');
  const [grassOptions, setGrassOptions] = useState<GrassOption[]>([]);
  const [numericFields, setNumericFields] = useState(DEFAULT_FIELDS);
  const [mechanismOptions, setMechanismOptions] = useState(DEFAULT_MECHANISMS);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [loadingMetadata, setLoadingMetadata] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let isActive = true;

    async function loadPredictionData() {
      setLoadingMetadata(true);
      setError('');
      try {
        const [metadata, grasses] = await Promise.all([
          getPredictionMetadata(),
          getGrassOptions(),
        ]);

        if (!isActive) {
          return;
        }

        setGrassOptions(grasses.length > 0 ? grasses : metadata.available_species);
        setNumericFields(metadata.numeric_fields.length > 0 ? metadata.numeric_fields : DEFAULT_FIELDS);
        setMechanismOptions(metadata.mechanism_options.length > 0 ? metadata.mechanism_options : DEFAULT_MECHANISMS);
      } catch (loadError) {
        if (!isActive) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : 'Backend is not running or metadata could not be loaded.');
      } finally {
        if (isActive) {
          setLoadingMetadata(false);
        }
      }
    }

    loadPredictionData();

    return () => {
      isActive = false;
    };
  }, []);

  const selectedGrass = useMemo(
    () => grassOptions.find((grass) => grass.species === species),
    [grassOptions, species],
  );

  const validateForm = () => {
    if (mode === 'grass_based' && !species) {
      return 'Select a grass species before predicting.';
    }
    if (mode === 'mechanism_based' && !mechanism) {
      return 'Select a mechanism before predicting.';
    }
    if (!knownField) {
      return 'Select the known numeric field.';
    }
    if (knownValue.trim() === '') {
      return 'Enter the known value.';
    }
    const numericValue = Number(knownValue);
    if (!Number.isFinite(numericValue)) {
      return 'Enter a valid number for the known value.';
    }
    return '';
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validationMessage = validateForm();
    if (validationMessage) {
      setError(validationMessage);
      return;
    }

    setSubmitting(true);
    setError('');
    setResult(null);

    try {
      const prediction = await predictValues({
        mode,
        species: mode === 'grass_based' ? species : null,
        mechanism: mode === 'mechanism_based' ? mechanism : null,
        known_field: knownField,
        known_value: Number(knownValue),
      });
      setResult(prediction);
    } catch (predictionError) {
      setError(predictionError instanceof Error ? predictionError.message : 'Prediction request failed.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="library-page prediction-page">
      <header className="page-hero prediction-hero">
        <div>
          <p className="eyebrow">Phase 2 Model</p>
          <h1>Salt Tolerance Prediction</h1>
          <p className="page-subtitle">
            Estimate missing GR50 and ion concentration values using regression-based patterns from the cleaned 30-grass dataset.
          </p>
        </div>
      </header>

      <section className="prediction-layout">
        <form className="prediction-panel" onSubmit={handleSubmit}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Prediction Input</p>
              <h2>Choose Context and Known Value</h2>
            </div>
            <Activity aria-hidden="true" size={22} />
          </div>

          <div className="mode-selector" role="tablist" aria-label="Prediction mode">
            <button
              className={mode === 'grass_based' ? 'mode-button mode-button-active' : 'mode-button'}
              type="button"
              onClick={() => {
                setMode('grass_based');
                setResult(null);
              }}
            >
              Grass-Based Prediction
            </button>
            <button
              className={mode === 'mechanism_based' ? 'mode-button mode-button-active' : 'mode-button'}
              type="button"
              onClick={() => {
                setMode('mechanism_based');
                setResult(null);
              }}
            >
              Mechanism-Based Prediction
            </button>
          </div>
          <p className="mode-helper-text">
            {mode === 'grass_based'
              ? 'Uses the selected grass species profile to complete the remaining values.'
              : 'Uses similar grasses from the selected mechanism group to estimate missing values.'}
          </p>

          {loadingMetadata ? (
            <div className="inline-status">
              <Loader2 aria-hidden="true" size={18} />
              Loading prediction metadata...
            </div>
          ) : null}

          <div className="prediction-form-grid">
            {mode === 'grass_based' ? (
              <label className="filter-field">
                <span>Grass species</span>
                <select value={species} onChange={(event) => setSpecies(event.target.value)}>
                  <option value="">Select species</option>
                  {grassOptions.map((grass) => (
                    <option key={grass.species} value={grass.species}>
                      {grass.species} ({grass.common_name})
                    </option>
                  ))}
                </select>
              </label>
            ) : (
              <label className="filter-field">
                <span>Mechanism</span>
                <select value={mechanism} onChange={(event) => setMechanism(event.target.value)}>
                  <option value="">Select mechanism</option>
                  {mechanismOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
            )}

            <label className="filter-field">
              <span>Known field</span>
              <select value={knownField} onChange={(event) => setKnownField(event.target.value)}>
                {numericFields.map((field) => (
                  <option key={field} value={field}>
                    {formatFieldLabel(field)}
                  </option>
                ))}
              </select>
            </label>

            <label className="filter-field">
              <span>Known value</span>
              <input
                min="0"
                step="any"
                type="number"
                value={knownValue}
                placeholder="Enter numeric value"
                onChange={(event) => setKnownValue(event.target.value)}
              />
            </label>
          </div>

          {selectedGrass ? (
            <div className="prediction-context-note">
              Selected mechanism context: <strong>{selectedGrass.mechanism}</strong>
            </div>
          ) : null}

          {error ? (
            <div className="error-message" role="alert">
              <AlertCircle aria-hidden="true" size={18} />
              {error}
            </div>
          ) : null}

          <button className="primary-button" type="submit" disabled={submitting || loadingMetadata}>
            {submitting ? <Loader2 aria-hidden="true" size={17} /> : <Sprout aria-hidden="true" size={17} />}
            Predict Remaining Values
          </button>
        </form>

        <section className="prediction-panel prediction-note-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Model Note</p>
              <h2>Estimated Prediction</h2>
            </div>
          </div>
          <p>
            This prediction is an estimated value based on limited dataset patterns. It should be used for academic learning
            and comparison, not as a final biological measurement.
          </p>
          <p>
            Grass-based mode completes the selected species profile from the dataset. Mechanism-based mode estimates from
            similar grasses in the selected mechanism group.
          </p>
        </section>
      </section>

      {result ? (
        <section className="prediction-results" aria-labelledby="prediction-results-heading">
          <div className="results-header">
            <div>
              <p className="eyebrow">Predicted values</p>
              <h2 id="prediction-results-heading">Predicted Remaining Values</h2>
            </div>
            <span className="result-count">{result.model_used}</span>
          </div>

          {result.mode === 'grass_based' ? (
            <div className="prediction-context-note">
              Uses the selected grass as the base profile, then adjusts remaining values using learned regression patterns.
            </div>
          ) : null}

          {result.known_value_comparison ? (
            <div className="prediction-comparison-panel">
              <h3>Known value comparison</h3>
              <dl>
                <div>
                  <dt>Dataset value</dt>
                  <dd>{result.known_value_comparison.dataset_known_value}</dd>
                </div>
                <div>
                  <dt>Entered value</dt>
                  <dd>{result.known_value_comparison.user_known_value}</dd>
                </div>
                <div>
                  <dt>Difference</dt>
                  <dd>{result.known_value_comparison.difference}</dd>
                </div>
              </dl>
              <p>
                {Math.abs(result.known_value_comparison.difference) <= 0.000001
                  ? 'Entered value matches the stored dataset value, so predictions remain close to the selected species profile.'
                  : 'Entered value differs from the stored dataset value, so remaining values are regression-adjusted from the selected species profile.'}
              </p>
            </div>
          ) : null}

          <div className="prediction-result-grid">
            <PredictionGroup title="GR50" fields={['gr50_avg']} predictions={result.predictions} />
            <PredictionGroup title="Na+" fields={['na_shoot', 'na_root']} predictions={result.predictions} />
            <PredictionGroup title="Cl-" fields={['cl_shoot', 'cl_root']} predictions={result.predictions} />
            <PredictionGroup title="K+" fields={['k_shoot', 'k_root']} predictions={result.predictions} />
          </div>

          {result.similar_grasses.length > 0 ? (
          <section className="similar-grasses-section">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Similar Grasses</p>
                <h2>Nearest Records Used for Context</h2>
              </div>
            </div>
            <div className="similar-grass-grid">
              {result.similar_grasses.map((grass) => (
                <article className="similar-grass-card" key={`${grass.species}-${grass.similarity_note}`}>
                  <h3>{grass.species}</h3>
                  <p>{grass.common_name}</p>
                  <span className={`status-pill ${grass.mechanism === 'Salt-Secreting' ? 'status-pill-secreting' : 'status-pill-nonsecreting'}`}>
                    {grass.mechanism}
                  </span>
                  <small>{grass.similarity_note}</small>
                </article>
              ))}
            </div>
          </section>
          ) : null}

          <div className="prediction-context-note">{result.note}</div>
        </section>
      ) : null}
    </main>
  );
}
