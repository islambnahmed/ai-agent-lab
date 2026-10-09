import test from "node:test";
import assert from "node:assert/strict";

test("verified preview clears old live values on subsequent outage",async()=>{
  const elements=new Map();
  const element=id=>{
    if(!elements.has(id))elements.set(id,{textContent:"",innerHTML:"",className:"",disabled:false,handlers:{},classList:{toggle(){}},addEventListener(type,fn){this.handlers[type]=fn}});
    return elements.get(id);
  };
  const oldDocument=globalThis.document,oldFetch=globalThis.fetch;
  let offline=false;
  globalThis.document={getElementById:element,querySelectorAll:()=>[]};
  const now=Date.now();
  const start=Date.UTC(2026,0,1);
  const history={metal:"XAU",grain:"daily",unit:"USD per troy ounce",points:Array.from({length:180},(_,i)=>({t:new Date(now-(179-i)*86400000).toISOString(),price:4200+i}))};
  const spot={updated:new Date(now-60000).toISOString(),metals:[{symbol:"XAU",ask:4500,bid:4490}]};
  globalThis.fetch=async url=>{
    if(offline)throw Error("offline");
    return {ok:true,json:async()=>url.includes("history")?history:spot};
  };
  try{
    await import("../app_verified.mjs");
    await new Promise(resolve=>setTimeout(resolve,0));
    assert.match(element("ask").textContent,/\$/);
    assert.match(element("forecast").textContent,/\$/);
    assert.match(element("status").textContent,/حديثان/);
    offline=true;
    await element("refresh").handlers.click();
    assert.equal(element("ask").textContent,"—");
    assert.equal(element("forecast").textContent,"—");
    assert.equal(element("chart").innerHTML,"");
    assert.match(element("status").textContent,/غير متاحة/);
    assert.match(element("message").textContent,/spot_unavailable/);
  }finally{
    globalThis.document=oldDocument;globalThis.fetch=oldFetch;
  }
});
