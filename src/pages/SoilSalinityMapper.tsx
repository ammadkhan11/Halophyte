import { useEffect, useMemo, useState } from 'react';
import { Activity, CheckCircle2, Loader2, Map, Play, Satellite } from 'lucide-react';
import {
  generateSoilSalinityMap,
  getSoilSalinityStatus,
  type SoilSalinityStatus,
} from '../lib/soilSalinityApi';

function formatGenerationState(status: SoilSalinityStatus | null) {
  if (!status) {
    return 'Checking service';
  }
  if (status.generation_state === 'earth_engine_map_generated') {
    return 'Map available';
  }
  if (status.generation_state === 'demo_map_generated') {
    return 'Map available';
  }
  if (status.generation_state === 'assets_generated') {
    return 'Map data ready';
  }
  return 'Map data is being generated';
}

function formatEarthEngineState(status: SoilSalinityStatus | null) {
  if (!status) {
    return 'Checking service';
  }
  if (status.earth_engine.authenticated) {
    return 'Authenticated';
  }
  if (status.earth_engine.python_api_installed) {
    return 'Authentication required';
  }
  return 'Service preparing';
}

export default function SoilSalinityMapper() {
  const [selectedProvince, setSelectedProvince] = useState('Punjab and Sindh');
  const [status, setStatus] = useState<SoilSalinityStatus | null>(null);
  const [statusError, setStatusError] = useState('');
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
    setStatusError('');
    try {
      const nextStatus = await getSoilSalinityStatus();
      setStatus(nextStatus);
      setMapUrl(nextStatus.map_url);
    } catch (error) {
      setStatusError(error instanceof Error ? error.message : 'Could not load soil salinity mapper status.');
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
      setGenerateMessage(`Map generated with ${result.points_rendered} salinity points.`);
      await loadStatus();
    } catch (error) {
      setGenerateMessage(error instanceof Error ? 'Map service is preparing.' : 'Map data is being generated.');
    } finally {
      setGenerating(false);
    }
  };

  const assetsReady = status?.assets_ready ?? false;
  const eeReady = status?.earth_engine.authenticated ?? false;
  const generationState = formatGenerationState(status);
  const earthEngineState = formatEarthEngineState(status);
  const mapLabel = mapUrl ? 'Map available' : generationState;

  return (
    <main className="library-page soil-page">
      <header className="page-hero soil-hero">
        <div>
          <p className="eyebrow">Soil Salinity Mapping</p>
          <h1>Pakistan Soil Salinity Mapper</h1>
          <p className="page-subtitle">
            Generate a regional salinity grid, inspect point-level EC values, and review crop-zone guidance for Punjab
            and Sindh in a focused map workspace.
          </p>
        </div>
      </header>

      <section className="soil-layout soil-layout-single">
        <div className="soil-control-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Mapping Controls</p>
              <h2>Region and Map Run</h2>
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
            <div className={eeReady ? 'soil-status-card soil-status-ok' : 'soil-status-card'}>
              {eeReady ? <CheckCircle2 aria-hidden="true" size={18} /> : <Activity aria-hidden="true" size={18} />}
              <div>
                <span>Earth Engine</span>
                <strong>{earthEngineState}</strong>
                <p>{eeReady ? 'Remote processing is available.' : 'Local map generation is available.'}</p>
              </div>
            </div>

            <div className={assetsReady ? 'soil-status-card soil-status-ok' : 'soil-status-card'}>
              {assetsReady ? <CheckCircle2 aria-hidden="true" size={18} /> : <Activity aria-hidden="true" size={18} />}
              <div>
                <span>Generation state</span>
                <strong>{generationState}</strong>
                <p>Region layers, grid values, and map output are handled by the local mapper service.</p>
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
            Generate Map
          </button>

          {generateMessage ? (
            <div className="inline-status">{generateMessage}</div>
          ) : null}

          {statusError ? (
            <div className="inline-status" role="status">Map service is preparing.</div>
          ) : null}
        </div>
      </section>

      <section className="soil-map-section" aria-labelledby="soil-map-heading">
        <div className="results-header">
          <div>
            <p className="eyebrow">Map Output</p>
            <h2 id="soil-map-heading">Generated Salinity Map</h2>
          </div>
          <span className="result-count">{mapLabel}</span>
        </div>

        {cacheBustedMapUrl ? (
          <iframe className="soil-map-frame" title="Generated Pakistan soil salinity map" src={cacheBustedMapUrl} />
        ) : (
          <div className="soil-map-empty">
            <Map aria-hidden="true" size={34} />
            <h3>Map data is being generated</h3>
            <p>
              Select a region and run the mapper to display point-level salinity values.
            </p>
          </div>
        )}
      </section>
    </main>
  );
}
