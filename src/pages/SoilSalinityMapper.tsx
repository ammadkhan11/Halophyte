import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, CheckCircle2, ExternalLink, FileText, Loader2, Map, Play, Satellite, ShieldAlert } from 'lucide-react';
import {
  generateSoilSalinityMap,
  getSoilSalinityStatus,
  type SoilSalinityStatus,
} from '../lib/soilSalinityApi';

const NOTEBOOK_URL = '/modules/mini-projects/soil-salinity-crop-zoning/Soil_Salinity_Mapping_FIXED.ipynb';
const README_URL = '/modules/mini-projects/soil-salinity-crop-zoning/README.md';

function formatGenerationState(status: SoilSalinityStatus | null) {
  if (!status) {
    return 'Checking Python environment';
  }
  if (status.generation_state === 'map_generated') {
    return 'Map generated';
  }
  if (status.generation_state === 'assets_generated') {
    return 'Assets generated';
  }
  return 'Not generated yet';
}

export default function SoilSalinityMapper() {
  const [selectedProvince, setSelectedProvince] = useState('Punjab and Sindh');
  const [status, setStatus] = useState<SoilSalinityStatus | null>(null);
  const [statusError, setStatusError] = useState('');
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [generateMessage, setGenerateMessage] = useState('');
  const [mapUrl, setMapUrl] = useState<string | null>(null);

  const cacheBustedMapUrl = useMemo(() => {
    if (!mapUrl) {
      return null;
    }
    return `${mapUrl}?v=${encodeURIComponent(generateMessage || 'ready')}`;
  }, [generateMessage, mapUrl]);

  const loadStatus = async () => {
    setLoadingStatus(true);
    setStatusError('');
    try {
      const nextStatus = await getSoilSalinityStatus();
      setStatus(nextStatus);
      setMapUrl(nextStatus.map_url);
    } catch (error) {
      setStatusError(error instanceof Error ? error.message : 'Could not load soil salinity mapper status.');
    } finally {
      setLoadingStatus(false);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const handleGenerateMap = async () => {
    setGenerating(true);
    setGenerateMessage('');
    try {
      const result = await generateSoilSalinityMap(selectedProvince);
      setMapUrl(result.map_url);
      setGenerateMessage(
        `Map generated in ${result.mode.replace(/_/g, ' ')} mode with ${result.points_rendered} demo grid points.`,
      );
      await loadStatus();
    } catch (error) {
      setGenerateMessage(error instanceof Error ? error.message : 'Map generation failed.');
    } finally {
      setGenerating(false);
    }
  };

  const assetsReady = status?.assets_ready ?? false;
  const eeReady = status?.earth_engine.authenticated ?? false;
  const eeInstalled = status?.earth_engine.python_api_installed ?? false;
  const generationState = formatGenerationState(status);

  return (
    <main className="library-page soil-page">
      <header className="page-hero soil-hero">
        <div>
          <p className="eyebrow">Soil Salinity Mapping</p>
          <h1>Pakistan Soil Salinity Mapper</h1>
          <p className="page-subtitle">
            Local application for the Punjab and Sindh salinity workflow. It can generate a clearly labelled
            demo/simulation map locally, and it reports Earth Engine setup status for future authenticated satellite runs.
          </p>
        </div>
      </header>

      <section className="soil-alert" role="note">
        <ShieldAlert aria-hidden="true" size={20} />
        <p>
          {status?.scientific_notice ??
            'This mapper is a local application wrapper around satellite/region processing. EC prediction labels are placeholders until verified field EC measurements are supplied.'}
        </p>
      </section>

      <section className="soil-layout">
        <div className="soil-control-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Mapping Controls</p>
              <h2>Region and Pipeline</h2>
            </div>
            <Satellite aria-hidden="true" size={22} />
          </div>

          <label className="filter-field">
            <span>Mapping region</span>
            <select value={selectedProvince} onChange={(event) => setSelectedProvince(event.target.value)}>
              <option value="Punjab and Sindh">Punjab and Sindh</option>
              <option value="Punjab">Punjab</option>
              <option value="Sindh">Sindh</option>
            </select>
          </label>

          <div className="soil-status-grid">
            <div className={eeReady ? 'soil-status-card soil-status-ok' : 'soil-status-card soil-status-warn'}>
              {eeReady ? <CheckCircle2 aria-hidden="true" size={18} /> : <AlertCircle aria-hidden="true" size={18} />}
              <div>
                <span>Earth Engine</span>
                <strong>
                  {eeReady ? 'Authenticated' : eeInstalled ? 'Not authenticated' : 'Not installed'}
                </strong>
                <p>{status?.earth_engine.message ?? 'Backend status is not available yet.'}</p>
              </div>
            </div>

            <div className={assetsReady ? 'soil-status-card soil-status-ok' : 'soil-status-card soil-status-warn'}>
              {assetsReady ? <CheckCircle2 aria-hidden="true" size={18} /> : <AlertCircle aria-hidden="true" size={18} />}
              <div>
                <span>Generation state</span>
                <strong>{generationState}</strong>
                <p>
                  Generate Local Map writes salinity grid, province GeoJSON, and map HTML into the module output folder.
                </p>
              </div>
            </div>
          </div>

          {status?.required_assets ? (
            <dl className="soil-asset-list">
              {status.required_assets.map((asset) => (
                <div key={asset.name}>
                  <dt>{asset.name}</dt>
                  <dd className={asset.exists ? 'soil-asset-ready' : 'soil-asset-missing'}>
                    {asset.exists ? 'Found' : 'Missing'}
                  </dd>
                </div>
              ))}
            </dl>
          ) : null}

          <button className="primary-button soil-run-button" type="button" onClick={handleGenerateMap} disabled={generating}>
            {generating ? <Loader2 aria-hidden="true" size={17} /> : <Play aria-hidden="true" size={17} />}
            Generate Local Map
          </button>

          {generateMessage ? (
            <div className={mapUrl ? 'prediction-context-note' : 'error-message'}>{generateMessage}</div>
          ) : null}

          {statusError ? (
            <div className="error-message" role="alert">
              <AlertCircle aria-hidden="true" size={18} />
              {statusError}
            </div>
          ) : null}
        </div>

        <aside className="soil-control-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Local Setup</p>
              <h2>Run Without Colab</h2>
            </div>
            <FileText aria-hidden="true" size={21} />
          </div>

          {loadingStatus ? (
            <div className="inline-status">
              <Loader2 aria-hidden="true" size={18} />
              Checking local mapper status...
            </div>
          ) : null}

          <ol className="soil-command-list">
            {(status?.setup_commands ?? [
              'python -m venv .venv',
              '.venv\\Scripts\\activate',
              'python -m pip install -r integrated\\soil-salinity-mapping\\requirements.txt',
              'python -c "import ee; print(\'ee ok\')"',
              'earthengine authenticate',
            ]).map((command) => (
              <li key={command}>
                <code>{command}</code>
              </li>
            ))}
          </ol>

          <div className="soil-link-row">
            <a className="secondary-button" href={NOTEBOOK_URL} target="_blank" rel="noreferrer">
              <ExternalLink aria-hidden="true" size={16} />
              Notebook reference
            </a>
            <a className="secondary-button" href={README_URL} target="_blank" rel="noreferrer">
              <ExternalLink aria-hidden="true" size={16} />
              Source notes
            </a>
          </div>
        </aside>
      </section>

      <section className="soil-map-section" aria-labelledby="soil-map-heading">
        <div className="results-header">
          <div>
            <p className="eyebrow">Map Output</p>
            <h2 id="soil-map-heading">Generated Salinity Map</h2>
          </div>
          <span className="result-count">{generationState}</span>
        </div>

        {cacheBustedMapUrl ? (
          <iframe className="soil-map-frame" title="Generated Pakistan soil salinity map" src={cacheBustedMapUrl} />
        ) : (
          <div className="soil-map-placeholder">
            <Map aria-hidden="true" size={34} />
            <h3>No generated local map yet</h3>
            <p>
              Click Generate Local Map to create local demo/simulation assets. This page does not display raw notebook
              cells or claim field-verified salinity accuracy.
            </p>
          </div>
        )}
      </section>
    </main>
  );
}
