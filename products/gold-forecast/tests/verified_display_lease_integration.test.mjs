import test from "node:test";
import assert from "node:assert/strict";

// Integration tests for the verified UI: use a fake clock and drive the actual
// timer/visibility callbacks, rather than testing the lease helper in isolation.
function harness({historyAvailable=true}={}) {
  const saved={document:globalThis.document,fetch:globalThis.fetch,setInterval:globalThis.setInterval,now:Date.now};
  const base=Date.parse("2026-10-10T12:00:00Z");
  let clock=base,tick,visible;
  const nodes=new Map();
  function el(id) {
    if(!nodes.has(id)) nodes.set(id,{
      textContent:"",innerHTML:"",className:"",disabled:false,handlers:{},
      classList:{toggle(){}},
      addEventListener(type,fn){this.handlers[type]=fn;}
    });
    return nodes.get(id);
  }
  globalThis.document={
    hidden:false,getElementById:el,querySelectorAll:()=>[],
    addEventListener(type,fn){if(type==="visibilitychange")visible=fn;}
  };
  globalThis.setInterval=(fn,ms)=>{assert.equal(ms,30_000);tick=fn;return {unref(){}};};
  Date.now=()=>clock;
  const history={
    metal:"XAU",grain:"daily",unit:"USD per troy ounce",
    points:Array.from({length:360},(_,i)=>({
      t:new Date(base-(359-i)*86400000).toISOString(),price:4000+i
    }))
  };
  const spot={
    unit:"USD per troy ounce",updated:new Date(base-60_000).toISOString(),
    metals:[{symbol:"XAU",ask:4500,bid:4490}]
  };
  globalThis.fetch=async url=>{
    if(url.includes("history")&&!historyAvailable) throw Error("history offline");
    return {ok:true,json:async()=>url.includes("history")?history:spot};
  };
  return {
    el,base,
    async ready(key){
      await import("../app_verified.mjs?lease-ui="+key);
      await new Promise(resolve=>setImmediate(resolve));
      assert.equal(typeof tick,"function");
      assert.equal(typeof visible,"function");
    },
    advance(ms){clock=base+ms;tick();},
    resume(ms){clock=base+ms;visible();},
    restore(){
      globalThis.document=saved.document;globalThis.fetch=saved.fetch;
      globalThis.setInterval=saved.setInterval;Date.now=saved.now;
    }
  };
}

test("verified UI expires quote independently, then forecast; DEMO remains exempt",async()=>{
  const h=harness();
  try{
    await h.ready("live");
    assert.match(h.el("status").textContent,/حديثان/);
    assert.match(h.el("ask").textContent,/\$/);
    assert.match(h.el("forecast").textContent,/\$/);
    h.advance(16*60_000);
    assert.equal(h.el("ask").textContent,"—");
    assert.equal(h.el("bid").textContent,"—");
    assert.match(h.el("forecast").textContent,/\$/);
    assert.match(h.el("status").textContent,/التاريخ متاح/);
    h.resume(8*86400000);
    assert.equal(h.el("forecast").textContent,"—");
    assert.equal(h.el("chart").innerHTML,"");
    assert.match(h.el("status").textContent,/غير متاحة/);
    h.el("demo").handlers.click();
    assert.match(h.el("status").textContent,/DEMO/);
    h.advance(30*86400000);
    assert.match(h.el("status").textContent,/DEMO/);
    assert.match(h.el("forecast").textContent,/\$/);
  }finally{h.restore();}
});

test("verified UI correctly tracks spot-only mode and expires its quote",async()=>{
  const h=harness({historyAvailable:false});
  try{
    await h.ready("spot");
    assert.match(h.el("status").textContent,/السعر اللحظي متاح/);
    assert.match(h.el("ask").textContent,/\$/);
    assert.equal(h.el("forecast").textContent,"—");
    h.advance(16*60_000);
    assert.equal(h.el("ask").textContent,"—");
    assert.match(h.el("status").textContent,/غير متاحة/);
  }finally{h.restore();}
});
