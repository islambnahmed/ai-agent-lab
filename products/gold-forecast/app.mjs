import {forecast,MODEL_NAMES} from "./forecast.mjs";
import {HISTORY_URL,SPOT_URL,CHECK_URL,prepareProviderHistory,prepareCsvHistory,validatedSpot,crossCheck} from "./data.mjs";

const HIST=HISTORY_URL;
const SPOT=SPOT_URL;
const el=id=>document.getElementById(id);
const usd=n=>Number.isFinite(n)?"$"+Number(n).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):"—";
const state={series:null,horizon:7,mode:"live",loading:false,epoch:0,result:null,asOf:null};

async function get(url){
  const ctrl=new AbortController(),timeout=setTimeout(()=>ctrl.abort(),12000);
  try{const response=await fetch(url,{signal:ctrl.signal,cache:"no-store"});
    if(!response.ok)throw Error("HTTP "+response.status);
    return await response.json();
  }finally{clearTimeout(timeout)}
}
function message(text){el("message").textContent=text}
function status(text){el("status").textContent=text}
function spotData(data){
  const {ask,bid,updated}=validatedSpot(data);
  el("ask").textContent=usd(ask);el("bid").textContent=usd(bid);
  el("updated").textContent="تاريخ السعر اللحظي UTC: "+updated;
}
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
  const labels='<text x="'+left+'" y="'+(h-7)+'" fill="#8999af" font-size="13">'+series[0].date+'</text><text x="'+lastx+'" y="'+(h-7)+'" text-anchor="middle" fill="#9aabc2" font-size="13">'+result.latest.date+'</text><text x="'+fx+'" y="'+(h-7)+'" text-anchor="end" fill="#e2bd7f" font-size="13">'+(result.targetDate||'+'+result.horizon+' closes')+'</text>';
  el("chart").innerHTML=grid.join("")+area+'<path d="'+d+'" fill="none" stroke="#d1d9e7" stroke-width="2.4" stroke-linejoin="round"/>'+future+labels;
}
function clearForecast(){
  for(const id of ["close","close-date","forecast","target","change","range","model","mae","base-mae","coverage","report"])el(id).textContent="—";
  el("change").className="change";el("chart").innerHTML="";el("candidates").replaceChildren();el("quality").textContent="—";state.result=null;el("export").disabled=true;
}
function render(){
  if(!state.series)return;
  try{
    const r=forecast(state.series,state.horizon,{asOf:state.asOf});
    state.result=r;el("export").disabled=false;
    r.horizon=state.horizon;
    el("close").textContent=usd(r.latest.price);
    el("close-date").textContent="إغلاق "+r.latest.date+" (غير السعر اللحظي)";
    el("forecast").textContent=usd(r.point);
    el("target").textContent=r.targetDate?"موعد تقريبي: "+r.targetDate+(r.calendar==="daily"?" (أيام تقويمية)":" (أيام عمل؛ دون تقويم عطلات بورصة)"):"بعد "+r.horizon+" إغلاقات مزوّد مستقبلية؛ الفجوات تمنع تحديد موعد موثوق.";
    const change=(r.point/r.latest.price-1)*100;
    el("change").textContent=(change>=0?"+":"")+change.toFixed(2)+"%";
    el("change").className="change "+(change>0.001?"up":change<-.001?"down":"");
    el("range").textContent=usd(r.lower)+" — "+usd(r.upper);
    el("model").textContent=MODEL_NAMES[r.model];
    el("mae").textContent=usd(r.audit.mae);
    el("base-mae").textContent=usd(r.baseline.mae);
    el("coverage").textContent=r.coverage.toFixed(1)+"%";
    el("report").textContent="اختيار على الفترة الأولى، ثم معايرة النطاق في فترة منفصلة، ثم اختبار "+r.audit.n+" توقعًا بعد "+r.auditedFrom+". الخطأ النسبي "+r.audit.mape.toFixed(2)+"%. "+
      (r.beat?"أقل خطأ من Baseline في هذه العينة فقط.":"لم يتفوق على Baseline في الاختبار.")+" عدد نوافذ الاختبار غير المتداخلة: "+r.disjoint.candidate.n+"؛ لا يعني أنها مستقلة. النطاق تجريبي وليس ضمانًا.";
    el("quality").textContent=r.dataQuality.rows+" إغلاق مكتمل. التتابع: "+(r.calendar==="daily"?"كل الأيام، بما فيها عطلة الأسبوع":r.calendar==="weekdays"?"أيام عمل":"غير منتظم؛ المدة بعدد الإغلاقات، وليست أيامًا أو جلسات بورصة")+". استُبعدت بيانات اليوم غير المكتمل. "+r.dataQuality.warnings.join(". ");
    el("candidates").replaceChildren();
    for(const c of r.candidates){
      const tr=document.createElement("tr");
      for(const value of [MODEL_NAMES[c.model],usd(c.validation.mae),c.validation.rmse.toFixed(2)]){const td=document.createElement("td");td.textContent=value;tr.appendChild(td);}
      el("candidates").appendChild(tr);
    }
    chart(r);
    if(state.mode==="live"){
      const stale=(Date.now()-Date.parse(r.latest.date+"T23:59:59Z"))/86400000;
      message(stale>7?"تنبيه: التاريخ السعري أقدم من أسبوع؛ التوقع ليس مبنيًا على السعر اللحظي.":"بحث تجريبي فقط: لا توجد أي ضمانات بأن التوقع سيتحقق.");
    }
  }catch(e){clearForecast();message("تعذر التنبؤ: "+e.message)}
}
async function refresh(){
  if(state.loading)return;const epoch=++state.epoch;state.loading=true;el("refresh").disabled=true;status("جاري جلب الأسعار");message("");
  state.mode="live";state.series=null;state.asOf=new Date().toISOString();clearForecast();
  el("ask").textContent="—";el("bid").textContent="—";el("updated").textContent="—";el("source").textContent="جارٍ تحميل مصدر الأسعار";el("crosscheck").textContent="جارٍ التحقق من مصدر ثانٍ";
  const [history,spot,secondary]=await Promise.allSettled([get(HIST),get(SPOT),get(CHECK_URL)]);
  if(epoch!==state.epoch){state.loading=false;el("refresh").disabled=false;return;}
  const errors=[];
  if(spot.status==="fulfilled"&&secondary.status==="fulfilled"){
    try{const check=crossCheck(validatedSpot(spot.value),secondary.value);el("crosscheck").textContent="Gold API: فرق السعر عن منتصف Ask/Bid = "+check.differencePct.toFixed(2)+"%. "+(check.status==="consistent_indicative_quotes"?"متقارب؛ أنواع الأسعار مختلفة.":"فرق كبير يحتاج مراجعة.");}
    catch(e){el("crosscheck").textContent="التحقق الثاني غير صالح: "+e.message;}
  }else el("crosscheck").textContent="المصدر الثاني غير متاح؛ لم يتم تأكيد السعر من مصدر آخر.";
  if(spot.status==="fulfilled"){try{spotData(spot.value)}catch(e){
    el("ask").textContent="—";el("bid").textContent="—";el("updated").textContent="السعر اللحظي غير متاح";
    errors.push("تعذر قراءة السعر اللحظي")
  }}
  else {el("ask").textContent="—";el("bid").textContent="—";el("updated").textContent="السعر اللحظي غير متاح";errors.push("السعر اللحظي غير متاح")}
  if(history.status==="fulfilled"){
    try{
      const prepared=prepareProviderHistory(history.value,state.asOf);
      const cleaned=prepared.series;
      forecast(cleaned,state.horizon,{asOf:state.asOf});
      state.series=cleaned;state.mode="live";
      el("source").textContent="إغلاقات مزوّد يومية وAsk/Bid من Standard Bullion. التوقع مبني على آخر يوم مكتمل، وليس السعر اللحظي.";
      render();
    }catch(e){errors.push("تعذر قراءة التاريخ: "+e.message)}
  }else errors.push("تعذر تحميل التاريخ السعري");
  if(!state.series)el("source").textContent="لم تُقبل بيانات تاريخية صالحة؛ لا يوجد توقع حي.";
  status(state.mode==="live"&&state.series?(errors.length?"البيانات جزئية":"متصل بمصدر السعر"):"المصدر غير متاح");
  if(errors.length)message(errors.join(" — ")+". جرّب DEMO أو CSV. الأسعار الحقيقية لن تُستبدل بأرقام وهمية تلقائيًا.");
  el("refresh").disabled=false;state.loading=false;
}
function demo(){
  ++state.epoch;
  const base=new Date();base.setUTCHours(12,0,0,0);base.setUTCDate(base.getUTCDate()-530);
  const series=[];let count=0;
  while(series.length<360){if(base.getUTCDay()!==0&&base.getUTCDay()!==6){series.push({date:base.toISOString().slice(0,10),price:2400+count*2.3+Math.sin(count*.13)*40+Math.cos(count*.73)*16});count++}base.setUTCDate(base.getUTCDate()+1)}
  state.series=series;state.mode="demo";state.asOf=new Date().toISOString();el("crosscheck").textContent="DEMO: لا يوجد تحقق من أسعار حقيقية";
  el("ask").textContent="—";el("bid").textContent="—";el("updated").textContent="لا يوجد سعر حي في وضع التجربة";
  el("source").textContent="DEMO: بيانات مولّدة برمجيًا وليست أسعار الذهب الحقيقية";
  status("DEMO — بيانات اصطناعية");render();message("تنبيه: جميع الأرقام التاريخية في هذا العرض وهمية للشرح فقط، ولا تُستخدم في الاستثمار.");
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
  const epoch=++state.epoch;
  try{
    const text=await file.text();
    if(epoch!==state.epoch){event.target.value="";return;}
    const asOf=new Date().toISOString();
    const prepared=prepareCsvHistory(text,asOf),series=prepared.series;forecast(series,state.horizon,{asOf});
    state.asOf=asOf;el("crosscheck").textContent="CSV محلي؛ مصدره غير موثّق";
    state.series=series;state.mode="csv";
    el("source").textContent="ملف محلي: "+file.name+" — لم يُرفع لخادم خارجي";
    el("ask").textContent="—";el("bid").textContent="—";el("updated").textContent="ملف CSV محلي";
    status("بيانات CSV محلية");render();
    message("كل النتائج من ملفك المحلي، ومصدره غير موثق من جانب الموقع.");
  }catch(e){if(epoch===state.epoch)message("مشكلة CSV: "+e.message)}
  event.target.value="";
});
el("export").addEventListener("click",()=>{
  if(!state.result)return;
  const blob=new Blob([JSON.stringify({mode:state.mode,asOf:state.asOf,...state.result},null,2)],{type:"application/json"});
  const link=document.createElement("a"),url=URL.createObjectURL(blob);link.href=url;link.download="gold-audit-"+state.horizon+".json";link.click();URL.revokeObjectURL(url);
});
refresh();
