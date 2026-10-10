import test from "node:test";
import assert from "node:assert/strict";

// Red-first UI regression: local selection must supersede an in-flight refresh.
// Run: node --test products/gold-forecast/tests/refresh_ownership_regression.test.mjs
function harness() {
  const previous={document:globalThis.document,fetch:globalThis.fetch};
  const nodes=new Map(),pending=[];
  function el(id){
    if(!nodes.has(id))nodes.set(id,{
      textContent:"",innerHTML:"",className:"",disabled:false,handlers:{},
      classList:{toggle(){}},
      addEventListener(type,fn){this.handlers[type]=fn;}
    });
    return nodes.get(id);
  }
  globalThis.document={getElementById:el,querySelectorAll:()=>[],addEventListener(){},hidden:false};
  globalThis.fetch=url=>new Promise(resolve=>pending.push({url,resolve}));
  return {el,pending,restore(){globalThis.document=previous.document;globalThis.fetch=previous.fetch;}};
}
async function settle(requests) {
  const now=Date.now();
  const history={metal:"XAU",grain:"daily",unit:"USD per troy ounce",
    points:Array.from({length:360},(_,i)=>({
      t:new Date(now-(359-i)*86400000).toISOString(),price:4100+i
    }))};
  const spot={unit:"USD per troy ounce",updated:new Date(now-60000).toISOString(),
    metals:[{symbol:"XAU",ask:4500,bid:4490}]};
  for(const p of requests)p.resolve({ok:true,json:async()=>p.url.includes("history")?history:spot});
  for(let i=0;i<20;i++)await Promise.resolve();
  await new Promise(resolve=>setImmediate(resolve));
}
test("invalid CSV releases old refresh lock; old completion cannot unlock new refresh",async()=>{
  const h=harness();
  try{
    await import("../app_verified.mjs?ownership=invalid");
    assert.equal(h.pending.length,2);
    await h.el("csv").handlers.change({target:{
      files:[{name:"bad.csv",text:async()=>"bad,columns\n1,2"}],value:"bad.csv"
    }});
    assert.match(h.el("message").textContent,/مشكلة CSV/);
    assert.equal(h.el("refresh").disabled,false,"local selection must release superseded lock");
    h.el("refresh").handlers.click();
    assert.equal(h.pending.length,4,"retry should launch a new provider request");
    assert.equal(h.el("refresh").disabled,true);
    await settle(h.pending.slice(0,2));
    assert.equal(h.el("refresh").disabled,true,"old request must not unlock newer refresh");
    await settle(h.pending.slice(2,4));
    assert.equal(h.el("refresh").disabled,false);
  }finally{h.restore();}
});
test("DEMO selection releases refresh lock without letting late responses overwrite it",async()=>{
  const h=harness();
  try{
    await import("../app_verified.mjs?ownership=demo");
    assert.equal(h.pending.length,2);
    h.el("demo").handlers.click();
    assert.equal(h.el("refresh").disabled,false);
    await settle(h.pending);
    assert.match(h.el("status").textContent,/DEMO/);
    assert.equal(h.el("refresh").disabled,false);
  }finally{h.restore();}
});
test("valid CSV can be replaced immediately by a fresh provider request",async()=>{
  const h=harness();
  try{
    await import("../app_verified.mjs?ownership=valid");
    const first=Date.now()-400*86400000;
    const rows=Array.from({length:360},(_,i)=>
      new Date(first+i*86400000).toISOString().slice(0,10)+","+(4100+i));
    await h.el("csv").handlers.change({target:{
      files:[{name:"valid.csv",text:async()=>"date,price\n"+rows.join("\n")}],
      value:"valid.csv"
    }});
    assert.match(h.el("status").textContent,/CSV/);
    assert.equal(h.el("refresh").disabled,false);
    h.el("refresh").handlers.click();
    assert.equal(h.pending.length,4);
    await settle(h.pending.slice(0,2));
    assert.equal(h.el("refresh").disabled,true);
    await settle(h.pending.slice(2,4));
    assert.equal(h.el("refresh").disabled,false);
  }finally{h.restore();}
});
