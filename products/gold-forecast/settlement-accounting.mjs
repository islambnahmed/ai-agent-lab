/**
 * Settlement accounting only, NOT verification of timestamp provenance or skill.
 * Every receipt remains in the denominator, including missing/quarantined rows.
 */
const HORIZONS=[1,7,30];
const STATUSES=new Set(['matured','pending','quarantined']);
const mean=(rows,key)=>rows.length?rows.reduce((sum,row)=>sum+row[key],0)/rows.length:null;

export function summarizeSettlements(receipts,outcomes){
  if(!Array.isArray(receipts)||!Array.isArray(outcomes))throw Error('Expected receipt and outcome arrays');
  const byId=new Map();
  for(const receipt of receipts){
    if(!receipt||typeof receipt.id!=='string'||!receipt.id||!HORIZONS.includes(receipt.horizon))
      throw Error('Invalid receipt accounting metadata');
    if(byId.has(receipt.id))throw Error('Duplicate receipt id: '+receipt.id);
    byId.set(receipt.id,receipt);
  }
  const outcomeById=new Map();
  for(const outcome of outcomes){
    if(!outcome||typeof outcome.id!=='string'||!byId.has(outcome.id))
      throw Error('Outcome without matching receipt');
    if(outcomeById.has(outcome.id))throw Error('Duplicate outcome id: '+outcome.id);
    if(!STATUSES.has(outcome.status))throw Error('Unknown outcome status: '+outcome.status);
    if(outcome.horizon!==undefined&&outcome.horizon!==byId.get(outcome.id).horizon)
      throw Error('Outcome horizon mismatch: '+outcome.id);
    if(outcome.status==='matured'){
      if(!['modelAbsError','baselineAbsError'].every(key=>Number.isFinite(outcome[key])&&outcome[key]>=0)
         ||typeof outcome.covered!=='boolean')throw Error('Invalid matured outcome metrics: '+outcome.id);
    }
    outcomeById.set(outcome.id,outcome);
  }
  return HORIZONS.map(horizon=>{
    const scoped=[...byId.values()].filter(receipt=>receipt.horizon===horizon);
    const statuses=scoped.map(receipt=>outcomeById.get(receipt.id)?.status??'unreported');
    const matured=scoped.map(receipt=>outcomeById.get(receipt.id)).filter(row=>row?.status==='matured');
    const count=status=>statuses.filter(x=>x===status).length;
    const coveredCount=matured.filter(x=>x.covered).length;
    const unknownCount=scoped.length-matured.length;
    return {horizon,totalReceipts:scoped.length,matured:count('matured'),pending:count('pending'),
      quarantined:count('quarantined'),unreported:count('unreported'),
      evaluatedPct:scoped.length?100*matured.length/scoped.length:null,
      modelMae:mean(matured,'modelAbsError'),baselineMae:mean(matured,'baselineAbsError'),
      coveragePct:matured.length?100*coveredCount/matured.length:null,
      // Unknown outcomes may all miss or all hit. These are recorded-outcome
      // accounting bounds, NOT independently prospective-verified coverage.
      allReceiptCoverageLowerPct:scoped.length?100*coveredCount/scoped.length:null,
      allReceiptCoverageUpperPct:scoped.length?100*(coveredCount+unknownCount)/scoped.length:null,
      prospectiveVerified:false,
      caveat:'Matured means algorithmically settled only; independent publication and price-close evidence is not verified here'};
  });
}
