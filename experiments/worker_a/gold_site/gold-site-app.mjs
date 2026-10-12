import {normalizeQuote,createBaseline,evaluatePending,appendIfNew,loadLedger} from './gold-site-core.mjs';
const $=id=>document.getElementById(id);
const fmt=n=>Number(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const statusText={pending:'بانتظار التقييم',expired:'انتهى دون نتيجة',evaluated:'تم التقييم'};
const MAX_REGISTER_DELAY_MS=15_000;
let current=null;
let ledger=[];
let storageHealthy=true;
try {ledger=loadLedger(localStorage.getItem('gold-lab-baselines-v1'));} catch { storageHealthy=false; $('message').textContent='سجل المتصفح تالف؛ تم إيقاف الحفظ لحماية البيانات القديمة.'; }
function save(){if(!storageHealthy){$('message').textContent='الحفظ متوقف لحماية السجل التالف من الكتابة فوقه.';return false;}try{localStorage.setItem('gold-lab-baselines-v1',JSON.stringify(ledger));return true;}catch{$('message').textContent='تعذر حفظ السجل في المتصفح.';return false;}}
function render(){
 const tbody=$('rows');tbody.replaceChildren();
 $('evaluated').textContent=String(ledger.filter(x=>x.status==='evaluated').length);
 if(!ledger.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=5;td.textContent='لا توجد توقعات مسجلة';tr.append(td);tbody.append(tr);return;}
 for(const f of [...ledger].reverse()){
  const tr=document.createElement('tr');
  for(const value of [f.issuedAt,f.targetAt,fmt(f.prediction),statusText[f.status]||'غير معروف',f.outcome?fmt(f.outcome.absoluteError):'—']){
   const td=document.createElement('td');td.textContent=value;tr.append(td);
  }tbody.append(tr);
 }
}
$('refresh').addEventListener('click',async()=>{
 const btn=$('refresh');btn.disabled=true;$('message').textContent='جارٍ طلب السعر...';
 const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),8000);
 try{
  const response=await fetch('https://api.gold-api.com/price/XAU',{headers:{Accept:'application/json'},signal:controller.signal,cache:'no-store'});
  if(!response.ok)throw Error('HTTP '+response.status);
  const payload=await response.json();const now=Date.now();current=normalizeQuote(payload,now);
  $('price').textContent=fmt(current.price)+' USD';$('sourceTime').textContent='وقت السعر: '+current.updatedAt;
  let f=null;try{f=createBaseline(current,now);}catch{}
  $('prediction').textContent=f?fmt(f.prediction)+' USD':'—';
  $('targetTime').textContent=f?'وقت الهدف: '+f.targetAt:'السعر قديم؛ لا يمكن إصدار توقع';
  $('register').disabled=!f;
  ledger=ledger.map(x=>evaluatePending(x,current));const persisted=save();render();
  $('message').textContent=(persisted?'وصل السعر. ':'وصل السعر لكن فشل حفظ السجل. ')+(f?'ممكن تسجّل توقعًا مرجعيًا.':'القراءة قديمة للتوقع.');
 }catch(e){current=null;$('register').disabled=true;$('price').textContent='—';$('sourceTime').textContent='لم يُحمّل سعر حديث';$('prediction').textContent='—';$('targetTime').textContent='لا يوجد توقع متاح';$('message').textContent='تعذر جلب السعر: '+e.message+' (لا توجد بيانات بديلة مفبركة).';}
 finally{clearTimeout(timeout);btn.disabled=false;}
});
$('register').addEventListener('click',()=>{
 if(!current)return;
 const issueMs=Date.now();
 const delay=issueMs-current.capturedMs;
 if(!Number.isFinite(delay)||delay<0||delay>MAX_REGISTER_DELAY_MS){
  $('register').disabled=true;
  $('message').textContent='انتهت مهلة تسجيل التوقع؛ حدّث السعر أولًا.';
  return;
 }
 try{const f=createBaseline(current,issueMs);const before=ledger;const next=appendIfNew(ledger,f);if(next===before){$('message').textContent='نفس قراءة السعر مسجلة بالفعل؛ لم نكرر التوقع.';return;}ledger=next;if(!save()){ledger=before;render();return;}render();$('targetTime').textContent='وقت الهدف: '+f.targetAt;$('message').textContent='تم حفظ التوقع في متصفحك فقط.';}
 catch(e){$('message').textContent=e.message;}
});
render();
