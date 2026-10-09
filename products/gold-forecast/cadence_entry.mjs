// Optional application adapter: preserves the existing import API while enforcing session cadence.
export {normalize,MODEL_NAMES,tradingDate} from './forecast.mjs';
export {guardedForecast as forecast} from './cadence_gate.mjs';
