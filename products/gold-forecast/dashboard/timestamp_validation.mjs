// Reject calendar-normalized and out-of-range offset-aware timestamps.
// Parsing alone is insufficient: some engines normalize impossible dates.
const ISO_OFFSET = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,3}))?(Z|([+-])(\d{2}):(\d{2}))$/;
const leap = year => year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
export function isValidOffsetTimestamp(value) {
  if (typeof value !== 'string') return false;
  const match = ISO_OFFSET.exec(value);
  if (!match) return false;
  const [, yy, mm, dd, hh, mi, ss, , zone, , oh, om] = match;
  const [year, month, day, hour, minute, second] = [yy, mm, dd, hh, mi, ss].map(Number);
  if (year < 1 || month < 1 || month > 12 || hour > 23 || minute > 59 || second > 59) return false;
  const days = [31, leap(year) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (day < 1 || day > days[month - 1]) return false;
  if (zone !== 'Z' && (Number(oh) > 14 || Number(om) > 59 || (Number(oh) === 14 && Number(om) !== 0))) return false;
  return Number.isFinite(Date.parse(value));
}
