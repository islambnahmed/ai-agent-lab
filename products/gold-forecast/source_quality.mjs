/** Strict third-party quote validation. Heuristic age thresholds are not provider SLAs. */
const positive = x => typeof x === "number" && Number.isFinite(x) && x > 0;
const DAY = 86400000;
function timestamp(value, label) {
  const m = typeof value === "string" && /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,3}))?(Z|[+-](?:(?:0\d|1[0-3]):[0-5]\d|14:00))$/.exec(value);
  if (!m) throw Error(label + ": explicit timezone ISO timestamp required");
  const [year,month,day,hour,minute,second] = m.slice(1,7).map(Number);
  const calendar = new Date(Date.UTC(year, month-1, day, hour, minute, second));
  if (calendar.getUTCFullYear()!==year || calendar.getUTCMonth()!==month-1 || calendar.getUTCDate()!==day ||
      calendar.getUTCHours()!==hour || calendar.getUTCMinutes()!==minute || calendar.getUTCSeconds()!==second)
    throw Error(label + ": invalid calendar date/time");
  const ms = Date.parse(value);
  if (!Number.isFinite(ms)) throw Error(label + ": invalid timestamp");
  return ms;
}
export function validateSpot(data, {nowMs=Date.now(), maxAgeMinutes=15}={}) {
  if (!Number.isFinite(nowMs) || !Number.isFinite(maxAgeMinutes) || maxAgeMinutes <= 0) throw Error("Invalid spot configuration");
  const metals = data?.metals;
  if (!Array.isArray(metals)) throw Error("Spot: missing metals");
  const gold = metals.find(m=>m?.symbol==="XAU");
  if (!gold || !positive(gold.ask) || !positive(gold.bid) || gold.ask < gold.bid) throw Error("Spot: invalid bid/ask");
  const updated = timestamp(data.updated, "Spot updated");
  if (updated-nowMs>120000) throw Error("Spot: future timestamp");
  const ageMinutes=Math.max(0,(nowMs-updated)/60000);
  return {quote:{ask:gold.ask,bid:gold.bid,updated:data.updated},state:ageMinutes>maxAgeMinutes?"stale":"fresh",ageMinutes};
}
export function validateHistory(data,{nowMs=Date.now(),maxAgeDays=7,minPoints=165}={}) {
  if (!Number.isFinite(nowMs)||!Number.isFinite(maxAgeDays)||maxAgeDays<=0||!Number.isInteger(minPoints)||minPoints<2) throw Error("Invalid history configuration");
  if (data?.metal!=="XAU"||!Array.isArray(data.points)) throw Error("History: expected XAU points");
  if (data.unit!=="USD per troy ounce") throw Error("History: explicit USD per troy ounce unit required");
  if (data.grain!=="daily") throw Error("History: explicit daily grain required");
  if (data.points.length<minPoints) throw Error("History: insufficient observations");
  let previous="";const rows=[];
  for (const p of data.points) {
    const ts=timestamp(p?.t,"History point");
    if (!positive(p?.price)) throw Error("History: invalid price");
    if (ts-nowMs>120000) throw Error("History: future observation");
    const date=new Date(ts).toISOString().slice(0,10);
    if (date<=previous) throw Error("History: duplicate or unsorted daily dates");
    previous=date;rows.push({date,price:p.price});
  }
  const ageDays=Math.max(0,(nowMs-Date.parse(previous+"T23:59:59Z"))/DAY);
  return {rows,latestDate:previous,ageDays,state:ageDays>maxAgeDays?"stale":"fresh"};
}
