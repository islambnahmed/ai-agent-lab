import {evaluateReceiptFile} from './prospective-io.mjs';
import {summarizeProspective} from './prospective-summary.mjs';

// Read/parse/settle errors become visible quarantines, never successes.
// Duplicate receipt IDs remain a hard failure rather than double-counting.
export function settleReceiptBatch(files,{readText,settle}){
  if(!Array.isArray(files)||files.some(f=>typeof f!=='string')||
     typeof readText!=='function'||typeof settle!=='function')
    throw Error('Invalid settlement batch arguments');
  const outcomes=files.filter(f=>f.endsWith('.json')).sort()
    .map(f=>evaluateReceiptFile(f,readText,settle));
  const summary=summarizeProspective(outcomes);
  return {outcomes,summaries:summary.summaries,summary};
}
