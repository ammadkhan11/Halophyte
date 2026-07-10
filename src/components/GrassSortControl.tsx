import type { GrassSortOption } from '../data/grassLibrarySearch';

type GrassSortControlProps = {
  value: GrassSortOption;
  onChange: (value: GrassSortOption) => void;
};

const sortOptions: Array<{ value: GrassSortOption; label: string }> = [
  { value: 'species-asc', label: 'Species A to Z' },
  { value: 'species-desc', label: 'Species Z to A' },
  { value: 'gr50-desc', label: 'Highest GR50' },
  { value: 'gr50-asc', label: 'Lowest GR50' },
  { value: 'salt-secreting-first', label: 'Salt-Secreting first' },
  { value: 'non-secreting-first', label: 'Non-Secreting first' },
  { value: 'na-shoot-desc', label: 'Highest Na+ Shoot' },
  { value: 'na-root-desc', label: 'Highest Na+ Root' },
  { value: 'cl-shoot-desc', label: 'Highest Cl- Shoot' },
  { value: 'cl-root-desc', label: 'Highest Cl- Root' },
  { value: 'k-shoot-desc', label: 'Highest K+ Shoot' },
  { value: 'k-root-desc', label: 'Highest K+ Root' },
];

export default function GrassSortControl({ value, onChange }: GrassSortControlProps) {
  return (
    <section className="sort-area" aria-label="Sort results">
      <label className="filter-field">
        <span>Sort</span>
        <select value={value} onChange={(event) => onChange(event.target.value as GrassSortOption)}>
          {sortOptions.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </label>
    </section>
  );
}
