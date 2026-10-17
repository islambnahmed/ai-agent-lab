// Presentation-only adapter. Never upgrades an evidence status.
import {FROZEN} from './evidence_snapshot.mjs';
const copy = {
  ar: {
    title:'توقعات الذهب — بحث تجريبي', intro:'توقعات مجمدة وليست أسعارًا مباشرة أو نصيحة استثمارية.',
    reference:'السعر المرجعي (16 أكتوبر 2026)', source:'مصدر السعر',
    horizons:'توقعات بعد عدد من قراءات المصدر، وليس أيامًا',
    pending:'قيد الانتظار — لا توجد نتيجة مؤكدة',
    unverified:'اكتملت القراءة — توقيت نشر النتيجة غير مثبت',
    error:'تعذر التحقق من البيانات؛ تم إيقاف عرض التوقعات.',
    noLive:'لا توجد تغذية أسعار مباشرة. ساعة المتصفح ليست إثباتًا مستقلًا لتوقيت النشر.',
    footer:'بحث فقط. لا يوجد دليل على دقة تنبؤية أو ربحية.',
    anchor:'سجل التوقعات الأصلي', unit:'دولار / أونصة تروي',
    score:'الخطأ المطلق: النموذج {c} دولار، السعر الثابت {b} دولار. هذه ليست نتيجة مثبتة زمنيًا.'
  },
  en: {
    title:'Gold forecasts — research prototype', intro:'Frozen research forecasts, not live quotes or investment advice.',
    reference:'Reference fixing (October 16, 2026)', source:'Price source',
    horizons:'Forecast horizons count provider observations, not calendar days',
    pending:'Pending — no confirmed outcome',
    unverified:'Observation matured — outcome publication time unverified',
    error:'Data validation failed; forecast display disabled.',
    noLive:'No live price feed. Browser time is not independent publication evidence.',
    footer:'Research only. Predictive skill and profitability are unproven.',
    anchor:'Original forecast anchor', unit:'USD / troy oz',
    score:'Absolute error: challenger ${c}, persistence ${b}. Timing remains unverified.'
  }
};
const money = n => Number.isFinite(n) ? n.toFixed(2) : null;
const validTimestamp = t => typeof t === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})$/.test(t) && Number.isFinite(Date.parse(t));
export function makeView(snapshot, lang='ar') {
  if (!['ar','en'].includes(lang)) throw Error('Unsupported language');
  if (!snapshot || snapshot.schemaVersion !== 1 || snapshot.forecastStatus !== 'research_only' ||
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
  let previousTargetDate = FROZEN.originDate;
  const forecasts = snapshot.forecasts.map((f,i) => {
    if (f.horizon !== [1,7,30][i] || f.point !== FROZEN.predictions[f.horizon] ||
        !['pending','matured_timing_unverified'].includes(f.status))
      throw Error('Unrecognized forecast status or horizon');
    if (f.status === 'pending') {
      if (snapshot.observedSinceOrigin >= f.horizon || f.observedSinceOrigin !== snapshot.observedSinceOrigin ||
          f.required !== f.horizon || f.baselineAbsoluteError !== undefined ||
          f.challengerAbsoluteError !== undefined || f.targetDate !== undefined ||
          f.improvementUsd !== undefined || f.directionCorrect !== undefined)
        throw Error('Inconsistent pending forecast');
    } else {
      const b = f.baselineAbsoluteError, c = f.challengerAbsoluteError;
      if (snapshot.observedSinceOrigin < f.horizon ||
          typeof f.targetDate !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(f.targetDate) ||
          f.targetDate <= previousTargetDate || f.targetDate > new Date(snapshot.generatedAsOf).toISOString().slice(0,10) ||
          !Number.isFinite(b) || !Number.isFinite(c) || b < 0 || c < 0 ||
          !Number.isFinite(f.improvementUsd) || Math.abs(f.improvementUsd-(b-c)) > 1e-7 ||
          typeof f.directionCorrect !== 'boolean' ||
          ![FROZEN.originPrice+b, FROZEN.originPrice-b].some(actual =>
            actual > 0 && Math.abs(Math.abs(f.point-actual)-c) < 1e-7 &&
            f.directionCorrect === (Math.sign(f.point-FROZEN.originPrice) === Math.sign(actual-FROZEN.originPrice))))
        throw Error('Inconsistent matured forecast score');
      previousTargetDate = f.targetDate;
    }
    const description = f.status === 'pending' ? s.pending : s.unverified;
    const score = f.status === 'pending' ? null : s.score.replace('{c}',money(f.challengerAbsoluteError)).replace('{b}',money(f.baselineAbsoluteError));
    return {horizon:f.horizon, price:money(f.point), status:f.status, description, score};
  });
  if (!Number.isFinite(snapshot.reference.price) || snapshot.reference.price <= 0) throw Error('Invalid reference');
  return {lang,dir:lang==='ar'?'rtl':'ltr',...s, referencePrice:money(snapshot.reference.price), forecasts,
    anchorUrl:'https://github.com/islambnahmed/ai-agent-lab/commit/'+snapshot.anchorCommit,
    sourceUrl:'https://www.westmetall.com/en/markdaten.php?action=table&field=USD_ozt_London&year=2026'};
}
