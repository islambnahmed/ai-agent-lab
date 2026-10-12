import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {forecast,MODEL_NAMES} from '../forecast.mjs';
import * as data from '../data.mjs';
const script=fs.readFileSync(new URL('../app.mjs',import.meta.url),'utf8').replace(/^import .*;\n/gm,'');
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
const flush=()=>new Promise(r=>setImmediate(r));
function harness(){
  const nodes=new Map();
  function node(id){return {id,textContent:'',innerHTML:'',disabled:false,children:[],handlers:{},dataset:{},classList:{toggle(){}},
    addEventListener(name,fn){this.handlers[name]=fn;},replaceChildren(){this.children=[];},appendChild(x){this.children.push(x);},click(){}};}
  const buttons=[1,7,30].map(h=>{const n=node('h'+h);n.dataset.h=String(h);return n;});
  const requests=[];
  const document={getElementById(id){if(!nodes.has(id))nodes.set(id,node(id));return nodes.get(id);},querySelectorAll(){return buttons;},createElement(){return node('new');}};
  const context=vm.createContext({forecast,MODEL_NAMES,...data,document,Date,Number,Math,Error,Promise,AbortController,Blob,URL,
    setTimeout:()=>0,clearTimeout:()=>{},fetch(url){const d=deferred();requests.push({url,...d});return d.promise;}});
  vm.runInContext(script+'\nglobalThis.view={state,refresh,demo};',context);
  const answer=(index,payload)=>requests[index].resolve({ok:true,json:async()=>payload});
  return {nodes,buttons,requests,answer,view:context.view};
}
function recent(n=300){
  const start=new Date();start.setUTCDate(start.getUTCDate()-n);
  return Array.from({length:n},(_,i)=>({date:new Date(start.valueOf()+i*86400000).toISOString().slice(0,10),price:2500+i}));
}
const history=()=>({metal:'XAU',grain:'daily',unit:data.UNIT,attribution:'Data by Standard Bullion',points:recent()});
const spot=()=>({unit:data.UNIT,updated:new Date().toISOString(),metals:[{symbol:'XAU',ask:2501,bid:2499}]});
const secondary=()=>({symbol:'XAU',price:2500,updatedAt:new Date().toISOString()});

test('real application accepts a correctly formatted current live quote',async()=>{
  const h=harness();h.answer(0,history());h.answer(1,spot());h.answer(2,secondary());await flush();
  assert.equal(h.view.state.mode,'live');assert.match(h.nodes.get('ask').textContent,/2,501/);
  assert.equal(h.view.state.result.dataQuality.rows,300);assert.equal(h.nodes.get('candidates').children.length,4);
});
test('delayed live response cannot overwrite DEMO choice',async()=>{
  const h=harness();h.view.demo();h.answer(0,history());h.answer(1,spot());h.answer(2,secondary());await flush();
  assert.equal(h.view.state.mode,'demo');assert.match(h.nodes.get('status').textContent,/DEMO/);
  assert.equal(h.nodes.get('ask').textContent,'—');
});
test('shorter-horizon CSV preflight is valid while live fetch is pending',async()=>{
  const h=harness(),rows=recent(170),csv=['date,price',...rows.map(r=>r.date+','+r.price)].join('\n');
  const target={files:[{name:'local.csv',text:async()=>csv}],value:'file'};
  await h.nodes.get('csv').handlers.change({target});
  h.answer(0,history());h.answer(1,spot());h.answer(2,secondary());await flush();
  assert.equal(h.view.state.mode,'csv');assert.equal(h.view.state.series.length,170);assert.equal(h.view.state.result.horizon,7);
});
test('late CSV read and late CSV failure cannot overwrite a later DEMO choice',async()=>{
  const h=harness(),d=deferred(),target={files:[{name:'late.csv',text:()=>d.promise}],value:'file'};
  const reading=h.nodes.get('csv').handlers.change({target});h.view.demo();d.resolve('bad csv');await reading;
  assert.equal(h.view.state.mode,'demo');assert.match(h.nodes.get('message').textContent,/وهمية/);
});
test('invalid fulfilled quote clears old fields and failed refresh clears old forecasts',async()=>{
  const h=harness();h.answer(0,history());h.answer(1,spot());h.answer(2,secondary());await flush();
  const refresh=h.view.refresh();
  h.answer(3,{metal:'XAU',points:[]});h.answer(4,{...spot(),updated:'bad'});h.answer(5,secondary());await refresh;
  assert.equal(h.nodes.get('ask').textContent,'—');assert.equal(h.nodes.get('forecast').textContent,'—');assert.equal(h.view.state.series,null);
});
