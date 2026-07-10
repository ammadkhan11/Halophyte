import { Search } from 'lucide-react';

type GrassSearchBarProps = {
  value: string;
  resultCount: number;
  totalCount: number;
  onChange: (value: string) => void;
};

export default function GrassSearchBar({ value, resultCount, totalCount, onChange }: GrassSearchBarProps) {
  return (
    <section className="search-area" aria-label="Species search">
      <div className="control-label-row">
        <label className="field-label" htmlFor="grass-search">
          Search
        </label>
        <span className="result-count">{resultCount} of {totalCount} results</span>
      </div>
      <div className="search-input-wrap">
        <Search aria-hidden="true" size={18} />
        <input
          id="grass-search"
          type="search"
          value={value}
          placeholder="Search by species name"
          onChange={(event) => onChange(event.target.value)}
        />
      </div>
    </section>
  );
}
