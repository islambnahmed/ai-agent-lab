/** Strict, offline parser for UNVERIFIED local gold-price CSV.
 * No source authentication or market-data validation is implied.
 * Supported: unquoted date,price (YYYY-MM-DD) or timestamp,close (UTC ISO Z).
 */
function error(row, message) { throw Error('CSV row ' + row + ': ' + message); }
function dateToMs(value, row) {
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const ms=Date.parse(value);
    if (!Number.isFinite(ms) || new Date(ms).toISOString().slice(0,10)!==value)
      error(row,'invalid calendar date');
    return ms;
  }
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(value)) {
    const ms=Date.parse(value);
    if (!Number.isFinite(ms) || new Date(ms).toISOString() !== (value.includes('.')?value:value.replace('Z','.000Z')))
      error(row,'invalid UTC timestamp');
    return ms;
  }
  error(row,'use YYYY-MM-DD or UTC timestamp ending Z');
}
export function parseGoldCsv(input,{nowMs=Date.now(),minPoints=165,maxRows=10000}={}) {
  if (typeof input!=='string') throw Error('CSV input must be text');
  if (!Number.isFinite(nowMs) || !Number.isInteger(minPoints) || minPoints<1 ||
      !Number.isInteger(maxRows) || maxRows<minPoints) throw Error('Invalid CSV parser configuration');
  const lines=input.replace(/^\uFEFF/,'').trim().split(/\r?\n/);
  const header=lines.shift().toLowerCase().split(',').map(x=>x.trim());
  const dateCols=header.map((s,i)=>['date','t','timestamp'].includes(s)?i:-1).filter(i=>i>=0);
  const priceCols=header.map((s,i)=>['price','close'].includes(s)?i:-1).filter(i=>i>=0);
  if (dateCols.length!==1 || priceCols.length!==1 || new Set(header).size!==header.length)
    throw Error('CSV requires exactly one date/timestamp and one price/close column');
  if (lines.length>maxRows) throw Error('CSV too large');
  const [di,pi]=[dateCols[0],priceCols[0]],result=[];
  let prevMs=-Infinity;
  const today=new Date(nowMs).toISOString().slice(0,10);
  for (let i=0;i<lines.length;i++) {
    const row=i+2,values=lines[i].split(',');
    if (values.length!==header.length) error(row,'column count mismatch');
    const rawDate=values[di].trim(),rawPrice=values[pi].trim();
    const ms=dateToMs(rawDate,row),day=new Date(ms).toISOString().slice(0,10);
    if (day>today || ms>nowMs) error(row,'future observation');
    if (ms<=prevMs || (result.length && day<=result.at(-1).date))
      error(row,'dates must be strictly increasing and unique by UTC day');
    const price=Number(rawPrice);
    if (!rawPrice || !Number.isFinite(price) || price<=0) error(row,'invalid positive price');
    result.push({date:day,price});prevMs=ms;
  }
  if (result.length<minPoints) throw Error('CSV needs at least '+minPoints+' valid observations');
  return result;
}
