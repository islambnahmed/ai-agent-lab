import {forecast,normalize,MODEL_NAMES,tradingDate} from "./forecast.mjs";
import {classifyFeeds} from "./feed_gate.mjs";

const HIST="https://standardbullion.com/api/v1/market/history?metal=XAU&range=1y";
const SPOT="https://standardbullion.com/spot-prices.json";
const el=id=>document.getElementById(id);
const usd=n=>Number.isFinite(n)?"$"+Number(n).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):"—";
const state={series:null,horizon:7,mode:"live",loading:false};

async function get(url){
  const ctrl=new AbortController(),timeout=setTimeout(()=>ctrl.abort(),12000);
  try{const response=await fetch(url,{signal:ctrl.signal,cache:"no-store"});
    if(!response.ok)throw Error("HTTP "+response.status);
    return await response.json();
  }finally{clearTimeout(timeout)}
}
function message(text){el("message").textContent=text}
function status(text){el("status").textContent=text}
function chart(result){
  const series=result.series,w=920,h=310,left=65,right=25,top=15,bottom=40;
  const tail=series.length-1;
  const x=i=>left+(w-left-right-95)*i/tail;
  const fx=w-right,lastx=x(tail);
  const values=series.map(p=>p.price).concat([result.point,result.lower,result.upper]);
  const mn=Math.min(...values),mx=Math.max(...values),pad=Math.max((mx-mn)*.14,mx*.004);
  const low=mn-pad,high=mx+pad;
  const y=v=>top+(high-v)/(high-low)*(h-top-bottom);
  const grid=[];
  for(let i=0;i<5;i++){
    const v=low+i*(high-low)/4,Y=y(v);
    grid.push('<line x1="'+left+'" y1="'+Y+'" x2="'+fx+'" y2="'+Y+'" stroke="#2e3d53" stroke-dasharray="4 6"/><text x="'+(left-9)+'" y="'+(Y+5)+'" fill="#96a4b9" font-size="13" text-anchor="end">'+Math.round(v).toLocaleString("en-US")+'</text>');
  }
  const d=series.map((p,i)=>(i?"L ":"M ")+x(i).toFixed(2)+" "+y(p.price).toFixed(2)).join(" ");
  const actual=series.at(-1).price;
  const area='<path d="M '+lastx+" "+y(actual)+" L "+fx+" "+y(result.upper)+" L "+fx+" "+y(result.lower)+' Z" fill="#d9b36d" fill-opacity=".17"/>';
  const future='<path d="M '+lastx+" "+y(actual)+" L "+fx+" "+y(result.point)+'" stroke="#edc783" stroke-width="3.5" stroke-dasharray="8 6" fill="none"/><circle cx="'+fx+'" cy="'+y(result.point)+'" r="5" fill="#edc783"/>';
  const labels='<text x="'+left+'" y="'+(h-7)+'" fill="#8999af" font-size="13">'+series[0].date+'</text><text x="'+lastx+'" y="'+(h-7)+'" text-anchor="middle" fill="#9aabc2" font-size="13">'+result.latest.date+'</text><text x="'+fx+'" y="'+(h-7)+'" text-anchor="end" fill="#e2bd7f" font-size="13">'+tradingDate(result.latest.date,result.horizon||state.horizon)+'</text>';
  el("chart").innerHTML=grid.join("")+area+'<path d="'+d+'" fill="none" stroke="#d1d9e7" stroke-width="2.4" stroke-linejoin="round"/>'+future+labels;
}
function render(){
  if(!state.series)return;
  try{
    const r=forecast(state.series,state.horizon);
    r.horizon=state.horizon;
    el("close").textContent=usd(r.latest.price);
    el("close-date").textContent="إغلاق "+r.latest.date+" (غير السعر اللحظي)";
    el("forecast").textContent=usd(r.point);
    el("target").textContent="تاريخ تقريبي: "+tradingDate(r.latest.date,state.horizon);
    const change=(r.point/r.latest.price-1)*100;
    el("change").textContent=(change>=0?"+":"")+change.toFixed(2)+"%";
    el("change").className="change "+(change>0.001?"up":change<-.001?"down":"");
    el("range").textContent=usd(r.lower)+" — "+usd(r.upper);
    el("model").textContent=MODEL_NAMES[r.model];
    el("mae").textContent=usd(r.audit.mae);
    el("base-mae").textContent=usd(r.baseline.mae);
    el("coverage").textContent=r.coverage.toFixed(1)+"%";
    el("report").textContent="تم اختيار النموذج على بيانات أقدم ثم اختبار "+r.audit.n+" توقعًا بعد "+r.auditedFrom+". خطأ النموذج النسبي "+r.audit.mape.toFixed(2)+"%. "+
      (r.beat?"تفوق على خط الأساس داخل هذه العينة فقط.":"لم يتفوق على خط الأساس في العينة المحجوزة.")+
      " النطاق التجريبي مبني على أخطاء سابقة؛ النوافذ المتداخلة ليست ملاحظات مستقلة.";
    chart(r);
    if(state.mode==="live"){
      const stale=(Date.now()-Date.parse(r.latest.date+"T23:59:59Z"))/86400000;
      message(stale>7?"تنبيه: التاريخ السعري أقدم من أسبوع؛ التوقع ليس مبنيًا على السعر اللحظي.":"بحث تجريبي فقط: لا توجد أي ضمانات بأن التوقع سيتحقق.");
    }
  }catch(e){message("تعذر التنبؤ: "+e.message)}
}
function clearFeed(){
  state.series=null;state.mode="unavailable";
  for(const id of ["ask","bid","close","forecast","target","change","range","model","mae","base-mae","coverage","updated"])el(id).textContent="—";
  el("close-date").textContent="لا توجد بيانات تاريخية موثوقة";
  el("chart").innerHTML="";el("change").className="change";
  el("report").textContent="لا توجد بيانات كافية لتقييم النموذج.";
  el("source").textContent="Standard Bullion — نتحقق من صلاحية كل تحديث قبل عرضه.";
}
async function refresh(){
  if(state.loading)return;
  state.loading=true;el("refresh").disabled=true;
  clearFeed();status("جاري جلب الأسعار");message("");
  try{
    const [history,spot]=await Promise.allSettled([get(HIST),get(SPOT)]);
    const gate=classifyFeeds(history,spot,{nowMs:Date.now()});
    if(gate.quote){
      el("ask").textContent=usd(gate.quote.ask);
      el("bid").textContent=usd(gate.quote.bid);
      el("updated").textContent="وقت السعر المعتمد UTC: "+gate.quote.updated;
    }else{
      el("updated").textContent=gate.quoteUpdated
        ?"آخر توقيت وصل: "+gate.quoteUpdated+" (السعر غير معتمد)"
        :"السعر اللحظي غير متاح";
    }
    if(gate.series){
      state.series=gate.series;state.mode=gate.state;
      el("source").textContent="إغلاقات تاريخية يومية وAsk/Bid من Standard Bullion؛ الأسعار عروض مزوّد وليست مرجعًا رسميًا.";
      render();
    }
    const labels={"live":"الأسعار والتاريخ حديثان بحسب حدود التحديث","history-only":"التاريخ متاح، السعر اللحظي غير موثوق","spot-only":"السعر اللحظي متاح، التوقع متوقف","unavailable":"البيانات غير متاحة"};
    status(labels[gate.state]);
    if(gate.problems.length)message("تنبيه: "+gate.problems.join(" — ")+". لا نعرض أسعارًا قديمة كأنها مباشرة. يمكنك استخدام DEMO أو CSV.");
  }catch(error){
    clearFeed();status("فشل تحديث البيانات");message("تعذر تحديث البيانات: "+error.message);
  }finally{state.loading=false;el("refresh").disabled=false}
}
function demo(){
  const base=new Date();base.setUTCHours(12,0,0,0);base.setUTCDate(base.getUTCDate()-530);
  const series=[];let count=0;
  while(series.length<360){if(base.getUTCDay()!==0&&base.getUTCDay()!==6){series.push({date:base.toISOString().slice(0,10),price:2400+count*2.3+Math.sin(count*.13)*40+Math.cos(count*.73)*16});count++}base.setUTCDate(base.getUTCDate()+1)}
  state.series=series;state.mode="demo";
  el("ask").textContent="—";el("bid").textContent="—";el("updated").textContent="لا يوجد سعر حي في وضع التجربة";
  el("source").textContent="DEMO: بيانات مولّدة برمجيًا وليست أسعار الذهب الحقيقية";
  status("DEMO — بيانات اصطناعية");render();message("تنبيه: جميع الأرقام التاريخية في هذا العرض وهمية للشرح فقط، ولا تُستخدم في الاستثمار.");
}
function parseCSV(text){
  const rows=text.replace(/^\uFEFF/,"").trim().split(/\r?\n/),header=rows.shift().toLowerCase().split(",").map(s=>s.trim());
  const di=header.findIndex(s=>["date","t","timestamp"].includes(s)),pi=header.findIndex(s=>["price","close"].includes(s));
  if(di<0||pi<0)throw Error("CSV must have date,price or Date,Close columns");
  return normalize(rows.map(line=>{const v=line.split(",");return {date:v[di],price:v[pi]}}));
}
for(const button of document.querySelectorAll("[data-h]")){
  button.addEventListener("click",()=>{
    state.horizon=Number(button.dataset.h);
    for(const b of document.querySelectorAll("[data-h]"))b.classList.toggle("chosen",b===button);
    render();
  });
}
el("refresh").addEventListener("click",refresh);
el("demo").addEventListener("click",demo);
el("csv").addEventListener("change",async event=>{
  const file=event.target.files?.[0];if(!file)return;
  try{
    const series=parseCSV(await file.text());forecast(series,30);
    state.series=series;state.mode="csv";
    el("source").textContent="ملف محلي: "+file.name+" — لم يُرفع لخادم خارجي";
    el("ask").textContent="—";el("bid").textContent="—";el("updated").textContent="ملف CSV محلي";
    status("بيانات CSV محلية");render();
    message("كل النتائج من ملفك المحلي، ومصدره غير موثق من جانب الموقع.");
  }catch(e){message("مشكلة CSV: "+e.message)}
  event.target.value="";
});
refresh();
