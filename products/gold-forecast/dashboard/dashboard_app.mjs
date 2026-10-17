import {buildSnapshot} from './evidence_snapshot.mjs';
import {makeView} from './dashboard_view.mjs';
const el=id=>document.getElementById(id);
let lang='ar';
function render(){
  // Empty observation feed: no live API and no outcome claims.
  // Client clock is only a rendering timestamp, never provider publication proof.
  el('cards').replaceChildren(); el('error').hidden=true;
  try {
    const view=makeView(buildSnapshot({asOf:new Date().toISOString(),observations:[]}),lang);
    document.documentElement.lang=view.lang; document.documentElement.dir=view.dir;
    for(const key of ['title','intro','footer','horizons']) el(key).textContent=view[key];
    el('notice').textContent=view.noLive;el('referenceLabel').textContent=view.reference;
    el('reference').textContent='$'+view.referencePrice;el('unit').textContent=view.unit;
    el('anchor').href=view.anchorUrl;el('anchor').textContent=view.anchor;
    el('source').href=view.sourceUrl;el('source').textContent=view.source;
    for(const f of view.forecasts){
      const article=document.createElement('article');article.className='card';
      const heading=document.createElement('h3');heading.textContent=(lang==='ar'?'بعد ':'After ')+f.horizon+(lang==='ar'?' قراءة':' observations');
      const price=document.createElement('div');price.className='price';price.textContent='$'+f.price;
      const status=document.createElement('p');status.className='state';status.textContent=f.description;
      article.append(heading,price,status);
      if(f.score){const score=document.createElement('p');score.textContent=f.score;article.append(score);}
      el('cards').append(article);
    }
  }catch(e){
    el('cards').replaceChildren();el('reference').textContent='';
    el('error').hidden=false;el('error').textContent=lang==='ar'?'تعذر التحقق من البيانات؛ تم إيقاف عرض التوقعات.':'Data validation failed; forecast display disabled.';
  }
  el('language').textContent=lang==='ar'?'English':'العربية';
}
el('language').addEventListener('click',()=>{lang=lang==='ar'?'en':'ar';render()});
render();
