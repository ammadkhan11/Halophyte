# Halophyte Grass Dictionary

Phase 1 frontend for the FYP Halophyte Grass Dictionary and Filtered Search Library.

## Run the React app

```bash
npm install
npm run dev
```

PowerShell may block the `npm` shim on some Windows machines. If that happens, use:

```bash
npm.cmd install
npm.cmd run dev
```

## Frontend structure

- `src/data/grassLibraryData.ts` - main TypeScript dataset used by the UI.
- `src/data/grassLibrarySearch.ts` - search and filtering helper.
- `src/pages/GrassLibrary.tsx` - main Grass Library page.
- `src/components/GrassSearchBar.tsx` - free-text search input.
- `src/components/GrassFilters.tsx` - mechanism, tolerance, GR50, Na+, Cl-, and K+ filters.
- `src/components/GrassSortControl.tsx` - sorting dropdown for species, GR50, mechanism, and ion values.
- `src/components/GrassCard.tsx` - mobile card view for grass records.
- `src/components/GrassDetailModal.tsx` - selected grass detail view.
- `src/components/GrassStats.tsx` - top summary cards.
- `src/components/UnitConversionHelper.tsx` - salinity and ion concentration conversion helper.
- `src/styles.css` - responsive academic UI styling.

## Dataset files

- `halophyte_grass_library.json` - main dataset for backend or frontend use.
- `halophyte_grass_library.csv` - same dataset in CSV format for review.
- `halophyte_grass_library_schema.json` - field definitions and filter configuration.
- `halophyte_grass_filter_config.json` - filter options only.
- `grassLibraryData.ts` - original TypeScript dataset file.
- `grassLibrarySearch.ts` - original TypeScript search/filter helper.
- `halophyte_grass_library_clean.xlsx` - review workbook with master data and filter configuration.

## Dataset summary

- Total records: 30
- Non-Secreting grasses: 20
- Salt-Secreting grasses: 10
- Missing numeric records after merge: 0

## Phase 1 scope

This phase includes dictionary browsing, species-name search, filters, sorting, statistics, unit conversion help, and a detailed record view. It does not include ML prediction.
