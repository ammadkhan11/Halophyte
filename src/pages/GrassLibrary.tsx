import { useMemo, useState } from 'react';
import { RotateCcw } from 'lucide-react';
import GrassCard from '../components/GrassCard';
import GrassDetailModal from '../components/GrassDetailModal';
import GrassFilters from '../components/GrassFilters';
import GrassSearchBar from '../components/GrassSearchBar';
import GrassSortControl from '../components/GrassSortControl';
import GrassStats from '../components/GrassStats';
import UnitConversionHelper from '../components/UnitConversionHelper';
import { grassLibraryData } from '../data/grassLibraryData';
import type { GrassLibraryRecord } from '../data/grassLibraryData';
import {
  defaultGrassSearchFilters,
  defaultGrassSortOption,
  searchGrassLibrary,
  sortGrassLibrary,
  type GrassSortOption,
  type GrassSearchFilters,
} from '../data/grassLibrarySearch';
import {
  cleanDisplayText,
  formatIonCategory,
  formatIonNumeric,
  formatNumber,
  formatRange,
} from '../utils/grassFormatters';

export default function GrassLibrary() {
  const [filters, setFilters] = useState<GrassSearchFilters>({ ...defaultGrassSearchFilters });
  const [sortOption, setSortOption] = useState<GrassSortOption>(defaultGrassSortOption);
  const [selectedGrass, setSelectedGrass] = useState<GrassLibraryRecord | null>(null);

  const results = useMemo(() => {
    const filteredResults = searchGrassLibrary(filters);
    return sortGrassLibrary(filteredResults, sortOption);
  }, [filters, sortOption]);

  const resetControls = () => {
    setFilters({ ...defaultGrassSearchFilters });
    setSortOption(defaultGrassSortOption);
  };

  return (
    <main className="library-page">
      <header className="page-hero">
        <div>
          <p className="eyebrow">Phase 1 Library</p>
          <h1>Halophyte Grass Dictionary</h1>
          <p className="page-subtitle">Academic reference library for salinity tolerance, secretion mechanisms, and ion accumulation profiles.</p>
        </div>
      </header>

      <GrassStats records={grassLibraryData} />

      <section className="library-controls" aria-label="Search filters and sorting">
        <div className="controls-row">
          <GrassSearchBar
            value={filters.query ?? ''}
            resultCount={results.length}
            totalCount={grassLibraryData.length}
            onChange={(query) => setFilters((currentFilters) => ({ ...currentFilters, query }))}
          />
          <GrassSortControl value={sortOption} onChange={setSortOption} />
          <button className="secondary-button reset-button" type="button" onClick={resetControls}>
            <RotateCcw aria-hidden="true" size={16} />
            Reset
          </button>
        </div>
        <GrassFilters filters={filters} onChange={setFilters} />
      </section>

      <section className="results-section" aria-labelledby="results-heading">
        <div className="results-header">
          <div>
            <p className="eyebrow">Grass Library</p>
            <h2 id="results-heading">Grass Records</h2>
          </div>
          <span className="result-count">{results.length} shown</span>
        </div>

        {results.length > 0 ? (
          <>
            <div className="table-shell">
              <table className="grass-table">
                <thead>
                  <tr>
                    <th>Species</th>
                    <th>Common Name</th>
                    <th>Mechanism</th>
                    <th>Salt Tolerance Level</th>
                    <th>GR50 Avg</th>
                    <th>GR50 Range</th>
                    <th>Na+ Shoot Numeric</th>
                    <th>Na+ Root Numeric</th>
                    <th>Na+ Category</th>
                    <th>Cl- Shoot Numeric</th>
                    <th>Cl- Root Numeric</th>
                    <th>Cl- Category</th>
                    <th>K+ Shoot Numeric</th>
                    <th>K+ Root Numeric</th>
                    <th>K+ Category</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((grass) => (
                    <tr key={grass.id}>
                      <td>
                        <strong>{cleanDisplayText(grass.scientific_name)}</strong>
                        <span>Record {grass.source_no}</span>
                      </td>
                      <td>{cleanDisplayText(grass.common_name)}</td>
                      <td>
                        <span className={`status-pill ${grass.is_salt_secreting ? 'status-pill-secreting' : 'status-pill-nonsecreting'}`}>
                          {grass.mechanism}
                        </span>
                      </td>
                      <td>{grass.salt_tolerance_level}</td>
                      <td>{formatNumber(grass.gr50_avg_ds_m)} dS/m</td>
                      <td>{formatRange(grass.gr50_min_ds_m, grass.gr50_max_ds_m)}</td>
                      <td>{formatIonNumeric(grass.na_shoot_mmol_kg_dw)}</td>
                      <td>{formatIonNumeric(grass.na_root_mmol_kg_dw)}</td>
                      <td>{formatIonCategory(grass.na_shoot_level, grass.na_root_level)}</td>
                      <td>{formatIonNumeric(grass.cl_shoot_mmol_kg_dw)}</td>
                      <td>{formatIonNumeric(grass.cl_root_mmol_kg_dw)}</td>
                      <td>{formatIonCategory(grass.cl_shoot_level, grass.cl_root_level)}</td>
                      <td>{formatIonNumeric(grass.k_shoot_mmol_kg_dw)}</td>
                      <td>{formatIonNumeric(grass.k_root_mmol_kg_dw)}</td>
                      <td>{formatIonCategory(grass.k_shoot_level, grass.k_root_level)}</td>
                      <td>
                        <button className="text-button" type="button" onClick={() => setSelectedGrass(grass)}>
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="grass-card-grid">
              {results.map((grass) => (
                <GrassCard key={grass.id} grass={grass} onSelect={setSelectedGrass} />
              ))}
            </div>
          </>
        ) : (
          <div className="empty-state">
            <h3>No grasses found</h3>
            <p>No records match the current search and filters.</p>
            <button className="secondary-button" type="button" onClick={resetControls}>
              Reset filters
            </button>
          </div>
        )}
      </section>

      <UnitConversionHelper />

      {selectedGrass && (
        <GrassDetailModal grass={selectedGrass} onClose={() => setSelectedGrass(null)} />
      )}
    </main>
  );
}
