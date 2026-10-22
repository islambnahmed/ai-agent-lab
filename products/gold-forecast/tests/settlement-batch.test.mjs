import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {issueReceipt,hash} from '../journal.mjs';
import {UNIT} from '../data.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const dates=n=>Array.from({length:n},(_,i)=>({
  date:new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10),
  price:2500+i*0.7+Math.sin(i*.15)*5
}));

test('settlement isolates malformed JSON while retaining valid matured outcomes',()=>{
  const temp=fs.mkdtempSync(path.join(os.tmpdir(),'gold-settle-cli-'));
  try{
    for(const folder of ['scripts','data','data/vintages','reports/prospective'])
      fs.mkdirSync(path.join(temp,folder),{recursive:true});
    for(const name of fs.readdirSync(root).filter(n=>n.endsWith('.mjs')))
      fs.copyFileSync(path.join(root,name),path.join(temp,name));
    fs.copyFileSync(path.join(root,'scripts','journal.mjs'),path.join(temp,'scripts','journal.mjs'));
    fs.writeFileSync(path.join(temp,'package.json'),JSON.stringify({type:'module'}));

    const frozen=dates(260);
    const receipt=issueReceipt(frozen,1,{
      issuedAt:'2025-09-18T12:00:00Z',
      source:'synthetic test fixture',
      codeCommit:'a'.repeat(40),
      sourceManifest:{receivedAt:'2025-09-18T11:59:00Z'}
    });
    fs.writeFileSync(path.join(temp,'data','vintages',receipt.historyHash+'.json'),JSON.stringify(frozen));
    const live={metal:'XAU',grain:'daily',unit:UNIT,attribution:'synthetic test fixture',points:dates(261)};
    fs.writeFileSync(path.join(temp,'data','history.json'),JSON.stringify(live));
    fs.writeFileSync(path.join(temp,'data','fetch-manifest.json'),JSON.stringify({
      history:{receivedAt:'2025-09-19T00:01:00Z'}
    }));

    const receipts=path.join(temp,'reports','prospective');
    fs.writeFileSync(path.join(receipts,'good.json'),JSON.stringify(receipt));
    fs.writeFileSync(path.join(receipts,'malformed.json'),'{"id":');
    fs.writeFileSync(path.join(receipts,'null.json'),'null');
    fs.writeFileSync(path.join(receipts,'array.json'),'[]');

    const run=spawnSync(process.execPath,[path.join(temp,'scripts','journal.mjs'),'settle'],{
      cwd:temp,encoding:'utf8',timeout:30000
    });
    assert.equal(run.status,0,run.stderr||run.stdout);
    const report=JSON.parse(run.stdout);
    assert.equal(report.outcomes.length,4);
    const matured=report.outcomes.filter(x=>x.status==='matured');
    assert.equal(matured.length,1);
    assert.equal(matured[0].id,receipt.id);
    assert.equal(matured[0].horizon,1);
    assert.equal(report.summaries.find(x=>x.horizon===1).matured,1);
    const quarantined=report.outcomes.filter(x=>x.status==='quarantined');
    assert.equal(quarantined.length,3);
    assert.deepEqual(quarantined.map(x=>x.file).sort(),['array.json','malformed.json','null.json']);
    for(const row of quarantined){
      assert.equal(row.id,null);
      assert.equal(row.horizon,null);
      assert.equal(typeof row.error,'string');
    }
    const persisted=JSON.parse(fs.readFileSync(path.join(temp,'runs','settlements.json'),'utf8'));
    assert.deepEqual(persisted,report);
  }finally{
    fs.rmSync(temp,{recursive:true,force:true});
  }
});
