import {validateHistoricalCloses,parseInstant,positivePrice} from './historical-integrity.mjs';
import {auditCalendar,targetDate} from './calendar_contract.mjs';

// Long range endpoints can downsample while still declaring "daily". Keep
// browser requests under a year; the research fetcher assembles dated chunks.
export const HISTORY_URL='https://standardbullion.com/api/v1/market/history?metal=XAU&range=1y';
export const SPOT_URL='https://standardbullion.com/spot-prices.json';
export const CHECK_URL='https://api.gold-api.com/price/XAU';
export const UNIT='USD per troy ounce';

// Calendar means observation cadence, not an exchange holiday calendar.
// Never drop valid weekend observations or fill missing prices to fit a label.
export function calendarOf(series){
  const calendar=series.some(p=>[0,6].includes(new Date(p.date+'T00:00:00Z').getUTCDay()))?'daily':'weekdays';
  const audit=auditCalendar(series,1,{calendar,warmup:1});
  return audit.unexpectedGaps?'observations':calendar;
}

export function prepareHistory(raw,{asOf=new Date().toISOString(),live=false,minRows=165}={}){
  const result=validateHistoricalCloses(raw,{asOf,minRows,requireFresh:live,maxAgeDays:7});
  if(result.series.length>10000)throw Error('History exceeds 10000 closes');
  const calendar=calendarOf(result.series);
  const jumps=result.series.slice(1).filter((p,i)=>Math.abs(p.price/result.series[i].price-1)>0.25).length;
  const gaps=result.series.slice(1).map((p,i)=>(Date.parse(p.date)-Date.parse(result.series[i].date))/86400000);
  const longestGap=Math.max(...gaps);
  if(longestGap>7)throw Error('Missing closes: gap exceeds 7 calendar days');
  return {...result,calendar,warnings:[...(jumps?['Large price jumps: '+jumps+'; check source or units']:[]),
    ...(calendar==='observations'?['Irregular provider cadence: horizons count observed closes; target date is unknown. No missing prices filled']:[]),
    ...(calendar==='daily'?['Provider uses calendar-day closes, including weekends']:[])]};
}

export function prepareProviderHistory(payload,asOf=new Date().toISOString()){
  if(!payload||payload.metal!=='XAU'||payload.unit!==UNIT||payload.grain!=='daily'||!Array.isArray(payload.points))
    throw Error('Expected daily XAU / USD per troy ounce history');
  if(typeof payload.attribution!=='string'||!payload.attribution.trim())throw Error('Missing data attribution');
  const result=prepareHistory(payload.points,{asOf,live:true});
  const oneDaySteps=result.series.slice(1).filter((p,i)=>Date.parse(p.date)-Date.parse(result.series[i].date)===86400000).length;
  if(oneDaySteps/(result.series.length-1)<0.5)throw Error('Suspected downsampled daily history: fetch smaller dated windows');
  return {...result,source:payload.source,attribution:payload.attribution};
}

export function prepareCsvHistory(text,asOf=new Date().toISOString()){
  if(typeof text!=='string'||text.length>2*1024*1024)throw Error('CSV limit is 2 MB');
  const lines=text.replace(/^\uFEFF/,'').trim().split(/\r?\n/);
  const cols=lines.shift().split(',').map(v=>v.trim().toLowerCase());
  const di=cols.findIndex(v=>['date','t','timestamp'].includes(v));
  const pi=cols.findIndex(v=>['price','close'].includes(v));
  if(di<0||pi<0||new Set(cols).size!==cols.length)throw Error('CSV needs unique date,price (USD/troy ounce) columns');
  const rows=lines.map((line,i)=>{
    const cells=line.split(',').map(v=>v.trim());
    if(cells.length!==cols.length||cells.some(v=>!v||v.includes('"')))throw Error('Malformed CSV row '+(i+2));
    return {date:cells[di],price:cells[pi]};
  });
  return prepareHistory(rows,{asOf});
}

export function validatedSpot(data,now=Date.now()){
  if(data?.unit!==UNIT)throw Error('Unexpected spot units');
  const gold=data?.metals?.find(m=>m.symbol==='XAU');
  const ask=positivePrice(gold?.ask),bid=positivePrice(gold?.bid);
  if(ask<bid)throw Error('Crossed dealer quote');
  const ts=parseInstant(data.updated,'Quote timestamp'),age=now-ts;
  if(age < -120000)throw Error('Future quote timestamp');
  if(age>30*60000)throw Error('Quote older than 30 minutes (may be market closure)');
  return {ask,bid,updated:data.updated};
}

export function crossCheck(primary,secondary,now=Date.now()){
  if(secondary?.symbol!=='XAU')throw Error('Cross-check symbol must be XAU');
  const price=positivePrice(secondary.price),stamp=secondary.updatedAt;
  const ts=parseInstant(stamp,'Secondary timestamp');
  if(now-ts>30*60000||now-ts < -120000)throw Error('Secondary quote not fresh');
  const primaryTs=parseInstant(primary.updated);
  if(Math.abs(primaryTs-ts)>5*60000)throw Error('Quotes more than 5 minutes apart');
  const midpoint=(primary.ask+primary.bid)/2;
  const differencePct=100*Math.abs(price/midpoint-1);
  return {source:'Gold API',price,updatedAt:stamp,differencePct,status:differencePct<=1?'consistent_indicative_quotes':'price_divergence',
    caveat:'Different price products; agreement does not authenticate historical closes or prove upstream independence'};
}
export {targetDate};
