import { useMemo, useState } from 'react';
import { Calculator } from 'lucide-react';

type ConversionOption = {
  value: string;
  label: string;
  outputUnit: string;
  convert: (value: number) => number;
};

const conversionOptions: ConversionOption[] = [
  {
    value: 'ds-to-ms',
    label: 'GR50 dS/m to mS/cm',
    outputUnit: 'mS/cm',
    convert: (value) => value,
  },
  {
    value: 'ds-to-us',
    label: 'GR50 dS/m to µS/cm',
    outputUnit: 'µS/cm',
    convert: (value) => value * 1000,
  },
  {
    value: 'na-to-mg-g',
    label: 'Na+ mmol kg^-1 to mg/g DW',
    outputUnit: 'mg/g DW',
    convert: (value) => (value * 22.99) / 1000,
  },
  {
    value: 'cl-to-mg-g',
    label: 'Cl- mmol kg^-1 to mg/g DW',
    outputUnit: 'mg/g DW',
    convert: (value) => (value * 35.45) / 1000,
  },
  {
    value: 'k-to-mg-g',
    label: 'K+ mmol kg^-1 to mg/g DW',
    outputUnit: 'mg/g DW',
    convert: (value) => (value * 39.1) / 1000,
  },
];

export default function UnitConversionHelper() {
  const [inputValue, setInputValue] = useState('1');
  const [conversionType, setConversionType] = useState(conversionOptions[0].value);

  const selectedConversion = conversionOptions.find((option) => option.value === conversionType) ?? conversionOptions[0];
  const convertedValue = useMemo(() => {
    if (inputValue.trim() === '') {
      return null;
    }

    const numericValue = Number(inputValue);

    if (Number.isNaN(numericValue)) {
      return null;
    }

    return selectedConversion.convert(numericValue);
  }, [inputValue, selectedConversion]);

  return (
    <section className="conversion-section" aria-labelledby="unit-conversion-heading">
      <div className="conversion-header">
        <div>
          <p className="eyebrow">Study Helper</p>
          <h2 id="unit-conversion-heading">Unit Conversion</h2>
        </div>
        <Calculator aria-hidden="true" size={22} />
      </div>

      <div className="conversion-content">
        <div className="conversion-notes">
          <div>
            <h3>GR50 / Salinity</h3>
            <p>1 dS/m = 1 mS/cm</p>
            <p>1 dS/m = 1000 µS/cm</p>
          </div>
          <div>
            <h3>Ion concentration</h3>
            <p>The dataset uses mmol kg^-1 Tissue DW.</p>
            <p>Na+ mg/g DW = mmol kg^-1 x 22.99 / 1000</p>
            <p>Cl- mg/g DW = mmol kg^-1 x 35.45 / 1000</p>
            <p>K+ mg/g DW = mmol kg^-1 x 39.10 / 1000</p>
          </div>
        </div>

        <div className="converter-panel" aria-label="Mini unit converter">
          <label className="filter-field">
            <span>Value</span>
            <input
              type="number"
              value={inputValue}
              step="0.1"
              onChange={(event) => setInputValue(event.target.value)}
            />
          </label>

          <label className="filter-field">
            <span>Conversion</span>
            <select value={conversionType} onChange={(event) => setConversionType(event.target.value)}>
              {conversionOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>

          <div className="conversion-result">
            <span>Result</span>
            <strong>
              {convertedValue == null ? 'Enter a number' : `${formatConversionResult(convertedValue)} ${selectedConversion.outputUnit}`}
            </strong>
          </div>
        </div>
      </div>
    </section>
  );
}

function formatConversionResult(value: number): string {
  return Number.isInteger(value) ? value.toString() : value.toFixed(4).replace(/\.?0+$/, '');
}
