// Presentation-only adapter. Never upgrades an evidence status.
import {FROZEN} from './evidence_snapshot.mjs';
const copy = {
  ar: {
    title:'توقعات الذهب — بحث تجريبي', intro:'توقعات مجمدة وليست أسعارًا مباشرة أو نصيحة استثمارية.',
    reference:'السعر المرجعي (16 أكتوبر 2026)', source:'مصدر السعر',
    horizons:'توقعات بعد عدد من قراءات المصدر، وليس أيامًا',
    pending:'قيد الانتظار — لا توجد نتيجة مؤكدة',
    unverified:'تسلسل قراءات المصدر غير مثبت — لا يمكن تقييم التوقع',
    error:'تعذر التحقق من البيانات؛ تم إيقاف عرض التوقعات.',
    noLive:'لا توجد تغذية أسعار مباشرة. ساعة المتصفح ليست إثباتًا مستقلًا لتوقيت النشر.',
    footer:'بحث فقط. لا يوجد دليل على دقة تنبؤية أو ربحية.',
    anchor:'سجل التوقعات الأصلي', unit:'دولار / أونصة تروي',
    score:'لا تتوفر نتيجة قابلة للتقييم.'
  },
  en: {
    title:'Gold forecasts — research prototype', intro:'Frozen research forecasts, not live quotes or investment advice.',
    reference:'Reference fixing (October 16, 2026)', source:'Price source',
    horizons:'Forecast horizons count provider observations, not calendar days',
    pending:'Pending — no confirmed outcome',
    unverified:'Provider observation sequence unverified — scoring withheld',
    error:'Data validation failed; forecast display disabled.',
    noLive:'No live price feed. Browser time is not independent publication evidence.',
    footer:'Research only. Predictive skill and profitability are unproven.',
    anchor:'Original forecast anchor', unit:'USD / troy oz',
    score:'No score is available.'
  }
};
const money = n => Number.isFinite(n) ? n.toFixed(2) : null;
const validTimestamp = t => typeof t === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})$/.test(t) && Number.isFinite(Date.parse(t));
export function makeView(snapshot, lang='ar') {
  if (!['ar','en'].includes(lang)) throw Error('Unsupported language');
  if (!snapshot || snapshot.schemaVersion !== 2 || snapshot.forecastStatus !== 'research_only' ||
      !snapshot.reference || snapshot.reference.unit !== 'USD/troy oz' ||
      !Array.isArray(snapshot.forecasts) || snapshot.forecasts.length !== 3 ||
      snapshot.anchorCommit !== FROZEN.anchorCommit || snapshot.batchId !== FROZEN.batchId ||
      snapshot.anchorCommittedAt !== FROZEN.anchorCommittedAt ||
      !validTimestamp(snapshot.generatedAsOf) || Date.parse(snapshot.generatedAsOf) < Date.parse(FROZEN.anchorCommittedAt) ||
      snapshot.reference.date !== FROZEN.originDate || snapshot.reference.price !== FROZEN.originPrice ||
      snapshot.reference.sourceId !== FROZEN.sourceId || snapshot.reference.session !== FROZEN.sourceSession ||
      !Number.isInteger(snapshot.observedSinceOrigin) || snapshot.observedSinceOrigin < 0 ||
      snapshot.observedSinceOrigin > 1000)
    throw Error('Invalid research snapshot');
  const s = copy[lang];
  const forecasts = snapshot.forecasts.map((f,i) => {
    if (f.horizon !== [1,7,30][i] || f.point !== FROZEN.predictions[f.horizon] ||
        !['pending','sequence_unverified'].includes(f.status))
      throw Error('Unrecognized forecast status or horizon');
    const expected = snapshot.observedSinceOrigin < f.horizon ? 'pending' : 'sequence_unverified';
    if (f.status !== expected || f.observedSinceOrigin !== snapshot.observedSinceOrigin ||
        f.required !== f.horizon ||
        ['baselineAbsoluteError','challengerAbsoluteError','targetDate','improvementUsd',
         'directionCorrect','caveat','actual','score'].some(k=>Object.hasOwn(f,k)))
      throw Error('Inconsistent unscored forecast');
    return {horizon:f.horizon, price:money(f.point), status:f.status,
      description:f.status==='pending'?s.pending:s.unverified, score:null};
  });
  if (!Number.isFinite(snapshot.reference.price) || snapshot.reference.price <= 0) throw Error('Invalid reference');
  return {lang,dir:lang==='ar'?'rtl':'ltr',...s, referencePrice:money(snapshot.reference.price), forecasts,
    anchorUrl:'https://github.com/islambnahmed/ai-agent-lab/commit/'+snapshot.anchorCommit,
    sourceUrl:'https://www.westmetall.com/en/markdaten.php?action=table&field=USD_ozt_London&year=2026'};
}
