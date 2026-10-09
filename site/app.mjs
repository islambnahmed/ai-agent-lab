/** Fail-closed forecast display contract. Validation is NOT independent source verification. */
const ISO_UTC = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;
const ISO_DAY = /^\d{4}-\d{2}-\d{2}$/;

function utc(value) {
  if (typeof value !== 'string' || !ISO_UTC.test(value)) return null;
  const d = new Date(value);
  return Number.isFinite(d.getTime()) && d.toISOString().replace('.000Z', 'Z') === value ? d : null;
}

function day(value) {
  if (typeof value !== 'string' || !ISO_DAY.test(value)) return null;
  const d = new Date(value + 'T00:00:00Z');
  return Number.isFinite(d.getTime()) && d.toISOString().slice(0, 10) === value ? d : null;
}

export function validateForecastManifest(m, now = new Date()) {
  const invalid = (reason) => ({ok: false, reason});
  if (!(now instanceof Date) || !Number.isFinite(now.getTime())) return invalid('invalid_clock');
  if (!m || typeof m !== 'object' || Array.isArray(m)) return invalid('missing_manifest');
  if (m.status !== 'publishable') return invalid('not_publishable');
  if (m.schema_version !== 1 || m.instrument !== 'gold_usd_per_troy_ounce') return invalid('schema_mismatch');
  if (typeof m.forecast_price !== 'number' || !Number.isFinite(m.forecast_price) || m.forecast_price <= 0) return invalid('invalid_price');
  if (typeof m.model_id !== 'string' || !/^[a-zA-Z0-9_.-]{1,80}$/.test(m.model_id)) return invalid('invalid_model');
  const asof = utc(m.as_of_utc), generated = utc(m.generated_at_utc), expires = utc(m.expires_at_utc), target = day(m.target_date);
  if (!asof || !generated || !expires || !target) return invalid('invalid_dates');
  if (asof > generated || generated > now || expires <= now || target <= asof) return invalid('invalid_timeline');
  let source;
  try { source = new URL(m.source_url); } catch { return invalid('invalid_source'); }
  if (source.protocol !== 'https:' || !source.hostname || source.username || source.password) return invalid('invalid_source');
  return {ok: true, view: {price: m.forecast_price, target: m.target_date, asof: m.as_of_utc, model: m.model_id, source: source.href}};
}

export function mount(root = document) {
  const get = (id) => root.getElementById(id);
  const text = (id, value) => { get(id).textContent = value; };
  const unavailable = (reason) => {
    text('status', 'لا يوجد توقع موثوق للعرض');
    text('price', '—');
    text('message', 'لا تتوفر بيانات مستوفية لشروط النشر حاليًا.');
    for (const id of ['target', 'asof', 'model']) text(id, '—');
    get('source').replaceChildren(root.createTextNode('غير متاح'));
    get('status').dataset.reason = reason;
  };
  unavailable('loading');
  fetch('./forecast.json', {cache: 'no-store'})
    .then((response) => { if (!response.ok) throw new Error('http_error'); return response.json(); })
    .then((data) => {
      const result = validateForecastManifest(data);
      if (!result.ok) return unavailable(result.reason);
      const v = result.view;
      text('status', 'توقع متاح وفق شروط النشر');
      text('price', new Intl.NumberFormat('ar-EG', {maximumFractionDigits: 2}).format(v.price));
      text('message', 'هذه قيمة متوقعة وليست سعر تداول لحظيًا.');
      text('target', v.target); text('asof', v.asof); text('model', v.model);
      const a = root.createElement('a'); a.href = v.source; a.textContent = 'عرض المصدر';
      a.rel = 'noopener noreferrer'; a.target = '_blank';
      get('source').replaceChildren(a);
    })
    .catch(() => unavailable('load_error'));
}

if (typeof document !== 'undefined') mount();
