// Isolate per-receipt read/parse/evaluation failures. A damaged file should
// quarantine that receipt without hiding outcomes from other receipt files.
import fs from 'node:fs';
import path from 'node:path';

export function evaluateReceiptFile(filename, evaluate) {
  if (typeof evaluate !== 'function') throw new TypeError('Receipt evaluator required');
  let receipt;
  try {
    receipt = JSON.parse(fs.readFileSync(filename, 'utf8'));
    return evaluate(receipt);
  } catch (error) {
    return {
      id: typeof receipt?.id === 'string' ? receipt.id : null,
      horizon: [1, 7, 30].includes(receipt?.horizon) ? receipt.horizon : null,
      file: path.basename(filename),
      status: 'quarantined',
      error: error instanceof Error ? error.message : String(error)
    };
  }
}
