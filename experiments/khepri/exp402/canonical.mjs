import crypto from 'node:crypto';

const KEY = /^[A-Za-z][A-Za-z0-9_]*$/;
const DECIMAL = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$/;
const MAX_DEPTH = 24, MAX_NODES = 10000, MAX_BYTES = 1024 * 1024;
export class InvalidPayload extends Error {}

export function canonicalDecimal(s) {
  if (typeof s !== 'string' || !DECIMAL.test(s)) throw new InvalidPayload('invalid decimal string');
  const sign = s.startsWith('-') ? '-' : '';
  const u = sign ? s.slice(1) : s;
  const [whole, fractional=''] = u.split('.');
  const fraction = fractional.replace(/0+$/, '');
  if (!/[1-9]/.test(whole + fraction)) return '0';
  return sign + whole + (fraction ? '.' + fraction : '');
}
function validUnicode(s) {
  for (let i=0; i<s.length; i++) {
    const c=s.charCodeAt(i);
    if (c>=0xD800 && c<=0xDBFF) {
      if (i+1>=s.length || s.charCodeAt(i+1)<0xDC00 || s.charCodeAt(i+1)>0xDFFF) return false;
      i++;
    } else if (c>=0xDC00 && c<=0xDFFF) return false;
  }
  return true;
}
export function canonicalBytes(v) {
  let count = 0;
  function walk(x, depth) {
    if (++count>MAX_NODES || depth>MAX_DEPTH) throw new InvalidPayload('complexity limit');
    if (x===null || typeof x==='boolean') return x;
    if (typeof x==='string') {
      if (!validUnicode(x)) throw new InvalidPayload('unpaired surrogate');
      return x;
    }
    if (Array.isArray(x)) return x.map(y=>walk(y,depth+1));
    if (typeof x==='object' && (Object.getPrototypeOf(x)===Object.prototype || Object.getPrototypeOf(x)===null)) {
      const out = {};
      for (const key of Object.keys(x).sort()) {
        if (!KEY.test(key)) throw new InvalidPayload('unsafe object key');
        out[key] = walk(x[key],depth+1);
      }
      return out;
    }
    throw new InvalidPayload('JSON numbers and non-JSON types prohibited');
  }
  const bytes=Buffer.from(JSON.stringify(walk(v,0)),'utf8');
  if (bytes.length>MAX_BYTES) throw new InvalidPayload('payload too large');
  return bytes;
}
export function digest(v) {return crypto.createHash('sha256').update(canonicalBytes(v)).digest('hex');}
export function goldPayload(id, amount, currency='USD', note='') {
  return {kind:'gold.receipt.issue', id, amount:canonicalDecimal(amount), currency, note};
}
export function seoPayload(id, page, wordCount, title) {
  return {kind:'seo.page.publish', id, page, wordCount:canonicalDecimal(wordCount), title};
}
