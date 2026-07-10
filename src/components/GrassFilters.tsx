import { grassFilterConfig, Mechanism, SaltToleranceLevel } from '../data/grassLibraryData';
import type { GrassSearchFilters, IonLevelFilter } from '../data/grassLibrarySearch';

type GrassFiltersProps = {
  filters: GrassSearchFilters;
  onChange: (filters: GrassSearchFilters) => void;
};

const mechanismOptions: Array<Mechanism | 'All'> = ['All', 'Non-Secreting', 'Salt-Secreting'];
const toleranceOptions: Array<SaltToleranceLevel | 'All'> = ['All', 'Low', 'Moderate', 'High', 'Very High'];
const ionOptions: IonLevelFilter[] = ['All', 'Low', 'Moderate', 'High'];

export default function GrassFilters({ filters, onChange }: GrassFiltersProps) {
  const updateFilters = (patch: Partial<GrassSearchFilters>) => {
    onChange({ ...filters, ...patch });
  };

  const updateNumberFilter = (key: 'gr50Min' | 'gr50Max', value: string) => {
    updateFilters({ [key]: value === '' ? undefined : Number(value) });
  };

  return (
    <section className="filter-area" aria-labelledby="grass-filter-heading">
      <h2 className="controls-subheading" id="grass-filter-heading">Filters</h2>
      <div className="filters-grid">
        <label className="filter-field">
          <span>Mechanism</span>
          <select
            value={filters.mechanism ?? 'All'}
            onChange={(event) => updateFilters({ mechanism: event.target.value as Mechanism | 'All' })}
          >
            {mechanismOptions.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>

        <label className="filter-field">
          <span>Salt tolerance</span>
          <select
            value={filters.toleranceLevel ?? 'All'}
            onChange={(event) => updateFilters({ toleranceLevel: event.target.value as SaltToleranceLevel | 'All' })}
          >
            {toleranceOptions.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>

        <label className="filter-field">
          <span>GR50 min</span>
          <input
            type="number"
            min={grassFilterConfig.gr50_range.min_ds_m}
            max={grassFilterConfig.gr50_range.max_ds_m}
            step="0.5"
            value={filters.gr50Min ?? ''}
            placeholder={String(grassFilterConfig.gr50_range.min_ds_m)}
            onChange={(event) => updateNumberFilter('gr50Min', event.target.value)}
          />
        </label>

        <label className="filter-field">
          <span>GR50 max</span>
          <input
            type="number"
            min={grassFilterConfig.gr50_range.min_ds_m}
            max={grassFilterConfig.gr50_range.max_ds_m}
            step="0.5"
            value={filters.gr50Max ?? ''}
            placeholder={String(grassFilterConfig.gr50_range.max_ds_m)}
            onChange={(event) => updateNumberFilter('gr50Max', event.target.value)}
          />
        </label>

        <label className="filter-field">
          <span>Na+ level</span>
          <select
            value={filters.naLevel ?? 'All'}
            onChange={(event) => updateFilters({ naLevel: event.target.value as IonLevelFilter })}
          >
            {ionOptions.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>

        <label className="filter-field">
          <span>Cl- level</span>
          <select
            value={filters.clLevel ?? 'All'}
            onChange={(event) => updateFilters({ clLevel: event.target.value as IonLevelFilter })}
          >
            {ionOptions.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>

        <label className="filter-field">
          <span>K+ level</span>
          <select
            value={filters.kLevel ?? 'All'}
            onChange={(event) => updateFilters({ kLevel: event.target.value as IonLevelFilter })}
          >
            {ionOptions.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>
      </div>
    </section>
  );
}
