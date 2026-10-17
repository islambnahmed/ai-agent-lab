import test from 'node:test';
import assert from 'node:assert/strict';
class Element {
  constructor(id=''){this.id=id;this.children=[];this.textContent='';this.hidden=false;this.handlers={};}
  replaceChildren(...nodes){this.children=[...nodes]}
  append(...nodes){this.children.push(...nodes)}
  addEventListener(event,fn){this.handlers[event]=fn}
}
test('app renders anchored pending forecasts, then switches language without changing values',async()=>{
  const ids=['cards','error','title','intro','footer','horizons','notice','referenceLabel','reference','unit','anchor','source','language'];
  const map=Object.fromEntries(ids.map(id=>[id,new Element(id)]));
  globalThis.document={documentElement:{lang:'ar',dir:'rtl'},getElementById:id=>map[id],createElement:tag=>new Element(tag)};
  try{
    await import('./dashboard_app.mjs');
    assert.equal(map.cards.children.length,3);
    assert.equal(map.reference.textContent,'$4181.90');
    assert.deepEqual(map.cards.children.map(card=>card.children[1].textContent),['$4176.90','$4168.68','$4154.57']);
    assert.ok(map.cards.children.every(card=>card.children[2].textContent.includes('قيد الانتظار')));
    assert.equal(map.error.hidden,true);
    assert.equal(map.anchor.href,'https://github.com/islambnahmed/ai-agent-lab/commit/609fc40a6233ea25ff1f6716a5bcc5df8c37f321');
    map.language.handlers.click();
    assert.equal(document.documentElement.lang,'en');
    assert.equal(document.documentElement.dir,'ltr');
    assert.deepEqual(map.cards.children.map(card=>card.children[1].textContent),['$4176.90','$4168.68','$4154.57']);
    assert.ok(map.cards.children.every(card=>card.children[2].textContent.includes('Pending')));
    assert.match(map.notice.textContent,/No live price feed/);
  }finally{delete globalThis.document;}
});
