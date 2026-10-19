const formatter = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 3 });
const energyFormatter = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 1 });
const coordinateFormatter = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 5 });
export const number = (value: number) => formatter.format(value);
export const energy = (value: number) => `${energyFormatter.format(value)} kWh`;
export const coordinate = (value: number) => coordinateFormatter.format(value);
