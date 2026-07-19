import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  FlaskConical,
  Loader2,
  Sprout,
  Waves,
} from 'lucide-react';
import {
  getBiosalineCrops,
  getBiosalineStatus,
  screenCropSalinity,
  type BiosalineCrop,
  type BiosalinePredictionResponse,
  type BiosalineStatus,
} from '../lib/biosalineApi';

const DEFAULT_INPUTS = {
  crop_id: 'wheat',
  ec_soil: 12,
  temperature: 38,
  rainfall_mm: 120,
};

function formatRange(range: [number, number] | null | undefined) {
  if (!range) {
    return 'Not listed';
  }
  return `${range[0]}-${range[1]} dS/m`;
}

function metricClass(riskLevel: string) {
  const normalized = riskLevel.toLowerCase();
  if (normalized === 'low') {
    return 'screening-risk-low';
  }
  if (normalized === 'medium') {
    return 'screening-risk-medium';
  }
  return 'screening-risk-high';
}

function YieldCurve({ result }: { result: BiosalinePredictionResponse }) {
  const points = result.yield_curve
    .map((point) => `${(point.ec_soil / 50) * 100},${100 - Math.max(0, Math.min(100, point.relative_yield_pct))}`)
    .join(' ');
  const currentX = (result.inputs.ec_soil / 50) * 100;
  const currentY = 100 - Math.max(0, Math.min(100, result.prediction.relative_yield_pct));

  return (
    <div className="screening-curve">
      <svg viewBox="0 0 100 100" role="img" aria-label="Yield response curve">
        <polyline points={points} />
        <line x1={result.crop.ec_threshold * 2} x2={result.crop.ec_threshold * 2} y1="0" y2="100" />
        <line className="screening-gr50-line" x1={result.crop.gr50 * 2} x2={result.crop.gr50 * 2} y1="0" y2="100" />
        <circle cx={currentX} cy={currentY} r="2.8" />
      </svg>
      <div className="screening-curve-labels">
        <span>0 dS/m</span>
        <span>50 dS/m</span>
      </div>
    </div>
  );
}

export default function CropSalinityScreening() {
  const [status, setStatus] = useState<BiosalineStatus | null>(null);
  const [crops, setCrops] = useState<BiosalineCrop[]>([]);
  const [cropId, setCropId] = useState(DEFAULT_INPUTS.crop_id);
  const [ecSoil, setEcSoil] = useState(String(DEFAULT_INPUTS.ec_soil));
  const [temperature, setTemperature] = useState(String(DEFAULT_INPUTS.temperature));
  const [rainfall, setRainfall] = useState(String(DEFAULT_INPUTS.rainfall_mm));
  const [result, setResult] = useState<BiosalinePredictionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const selectedCrop = useMemo(() => crops.find((crop) => crop.crop_id === cropId), [cropId, crops]);

  const runScreening = async (payloadCropId = cropId) => {
    const ecValue = Number(ecSoil);
    const temperatureValue = Number(temperature);
    const rainfallValue = Number(rainfall);

    if (!payloadCropId) {
      throw new Error('Select a crop before running the screening.');
    }
    if (![ecValue, temperatureValue, rainfallValue].every(Number.isFinite)) {
      throw new Error('Enter numeric values for salinity, temperature, and rainfall.');
    }

    return screenCropSalinity({
      crop_id: payloadCropId,
      ec_soil: ecValue,
      temperature: temperatureValue,
      rainfall_mm: rainfallValue,
    });
  };

  useEffect(() => {
    let isActive = true;

    async function loadModule() {
      setLoading(true);
      setError('');
      try {
        const nextStatus = await getBiosalineStatus();
        if (!isActive) {
          return;
        }
        setStatus(nextStatus);

        const cropResponse = await getBiosalineCrops();
        if (!isActive) {
          return;
        }
        const nextCrops = cropResponse.primary_crops.length > 0 ? cropResponse.primary_crops : cropResponse.all_crops;
        const defaultCrop = nextCrops.find((crop) => crop.crop_id === DEFAULT_INPUTS.crop_id) ?? nextCrops[0];
        setCrops(nextCrops);
        if (defaultCrop) {
          setCropId(defaultCrop.crop_id);
          const initialResult = await screenCropSalinity({ ...DEFAULT_INPUTS, crop_id: defaultCrop.crop_id });
          if (isActive) {
            setResult(initialResult);
          }
        }
      } catch (loadError) {
        if (isActive) {
          setError(loadError instanceof Error ? loadError.message : 'Crop salinity screening is not available.');
        }
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    }

    loadModule();
    return () => {
      isActive = false;
    };
  }, []);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      setResult(await runScreening());
      setStatus(await getBiosalineStatus());
    } catch (screeningError) {
      setError(screeningError instanceof Error ? screeningError.message : 'Screening request failed.');
    } finally {
      setSubmitting(false);
    }
  };

  const modelStatus = result?.model ?? status?.model;
  const datasetStatus = result?.dataset ?? status?.dataset;

  return (
    <main className="library-page screening-page">
      <header className="page-hero screening-hero">
        <div>
          <p className="eyebrow">Crop Salinity Risk Model</p>
          <h1>Crop Salinity Screening</h1>
          <p className="page-subtitle">
            Evaluate crop response under salinity, temperature, and rainfall conditions. Outputs focus on yield, risk,
            irrigation frequency, and alternative crops; financial metrics are intentionally omitted.
          </p>
        </div>
      </header>

      <section className="screening-layout">
        <form className="screening-panel" onSubmit={handleSubmit}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Screening Inputs</p>
              <h2>Crop and Salinity Scenario</h2>
            </div>
            <Sprout aria-hidden="true" size={22} />
          </div>

          {loading ? (
            <div className="inline-status">
              <Loader2 aria-hidden="true" size={18} />
              Loading crop salinity module...
            </div>
          ) : null}

          <div className="screening-form-grid">
            <label className="filter-field">
              <span>Crop</span>
              <select value={cropId} onChange={(event) => setCropId(event.target.value)} disabled={crops.length === 0}>
                {crops.length === 0 ? <option value="">No crops loaded</option> : null}
                {crops.map((crop) => (
                  <option key={crop.crop_id} value={crop.crop_id}>
                    {crop.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="filter-field">
              <span>Soil ECe / EC (dS/m)</span>
              <input min="0" max="50" step="0.1" type="number" value={ecSoil} onChange={(event) => setEcSoil(event.target.value)} />
            </label>

            <label className="filter-field">
              <span>Temperature (C)</span>
              <input
                min="15"
                max="45"
                step="0.5"
                type="number"
                value={temperature}
                onChange={(event) => setTemperature(event.target.value)}
              />
            </label>

            <label className="filter-field">
              <span>Seasonal rainfall (mm)</span>
              <input min="50" max="800" step="10" type="number" value={rainfall} onChange={(event) => setRainfall(event.target.value)} />
            </label>
          </div>

          {selectedCrop ? (
            <div className="screening-crop-summary">
              <dl>
                <div>
                  <dt>Scientific name</dt>
                  <dd>{selectedCrop.scientific_name}</dd>
                </div>
                <div>
                  <dt>Dataset EC range</dt>
                  <dd>{formatRange(selectedCrop.ec_range_tested)}</dd>
                </div>
                <div>
                  <dt>Dataset points</dt>
                  <dd>{selectedCrop.dataset_points}</dd>
                </div>
              </dl>
            </div>
          ) : null}

          {error ? (
            <div className="error-message" role="alert">
              <AlertCircle aria-hidden="true" size={18} />
              {error}
            </div>
          ) : null}

          <button className="primary-button" type="submit" disabled={submitting || loading || crops.length === 0}>
            {submitting ? <Loader2 aria-hidden="true" size={17} /> : <Activity aria-hidden="true" size={17} />}
            Run Screening
          </button>
        </form>

        <aside className="screening-panel screening-status-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Model Status</p>
              <h2>Data and Surrogate</h2>
            </div>
            <FlaskConical aria-hidden="true" size={21} />
          </div>

          <div className={modelStatus?.trained ? 'soil-status-card soil-status-ok' : 'soil-status-card'}>
            {modelStatus?.trained ? <CheckCircle2 aria-hidden="true" size={18} /> : <Activity aria-hidden="true" size={18} />}
            <div>
              <span>Surrogate ML</span>
              <strong>{modelStatus?.trained ? 'Trained model active' : 'Formula model active'}</strong>
              <p>{modelStatus?.trained ? 'Saved surrogate artifacts are loaded.' : 'Maas-Hoffman response is used for screening.'}</p>
            </div>
          </div>

          <div className={datasetStatus?.available ? 'soil-status-card soil-status-ok' : 'soil-status-card'}>
            {datasetStatus?.available ? <CheckCircle2 aria-hidden="true" size={18} /> : <Activity aria-hidden="true" size={18} />}
            <div>
              <span>Dataset</span>
              <strong>{datasetStatus?.rows ? `${datasetStatus.rows} rows` : datasetStatus?.available ? 'Found' : 'Preparing'}</strong>
              <p>
                {datasetStatus?.source_papers
                  ? `${datasetStatus.source_papers} source references loaded from the phase dataset.`
                  : datasetStatus?.message ?? 'Dataset status is loading.'}
              </p>
            </div>
          </div>
        </aside>
      </section>

      {result ? (
        <section className="screening-results" aria-labelledby="screening-results-heading">
          <div className="results-header">
            <div>
              <p className="eyebrow">Screening Output</p>
              <h2 id="screening-results-heading">{result.prediction.crop_name} Salinity Response</h2>
            </div>
            <span className={`status-pill ${metricClass(result.prediction.risk_level)}`}>{result.prediction.risk_level} risk</span>
          </div>

          <div className="screening-metrics">
            <div>
              <span>Expected yield</span>
              <strong>{result.prediction.expected_yield_t_ha.toFixed(2)} t/ha</strong>
            </div>
            <div>
              <span>Relative yield</span>
              <strong>{result.prediction.relative_yield_pct.toFixed(1)}%</strong>
            </div>
            <div>
              <span>Irrigation</span>
              <strong>{result.prediction.recommended_irrigation}</strong>
            </div>
            <div>
              <span>Confidence</span>
              <strong>{result.prediction.confidence}</strong>
            </div>
          </div>

          <div className="screening-detail-layout">
            <section>
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Yield Curve</p>
                  <h2>Maas-Hoffman Response</h2>
                </div>
                <Waves aria-hidden="true" size={21} />
              </div>
              <YieldCurve result={result} />
              <dl className="screening-threshold-list">
                <div>
                  <dt>EC threshold</dt>
                  <dd>{result.crop.ec_threshold} dS/m</dd>
                </div>
                <div>
                  <dt>GR50</dt>
                  <dd>{result.crop.gr50} dS/m</dd>
                </div>
                <div>
                  <dt>Model used</dt>
                  <dd>{result.prediction.model_used}</dd>
                </div>
              </dl>
            </section>

            <section>
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Alternatives</p>
                  <h2>Better Suited Crops</h2>
                </div>
              </div>
              {result.prediction.alternative_halophytes.length > 0 ? (
                <div className="screening-alternative-list">
                  {result.prediction.alternative_halophytes.map((crop) => (
                    <article key={crop.crop_id}>
                      <h3>{crop.name}</h3>
                      <p>{crop.scientific_name}</p>
                      <span>{crop.ec_threshold} dS/m threshold</span>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="prediction-context-note">Current crop remains suitable under this salinity scenario.</div>
              )}
            </section>
          </div>

          <div className="prediction-context-note">Screening scope: crop response, salinity risk, irrigation frequency, and crop alternatives.</div>
        </section>
      ) : null}
    </main>
  );
}
