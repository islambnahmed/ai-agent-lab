/** Explain disjoint holdout evidence without turning correlated windows into a skill claim. */
export function auditSummary(selected, audit) {
  if (!selected || !audit || selected.model !== audit.model ||
      selected.audit?.n !== audit.overlapping_audit_count ||
      !Number.isInteger(audit.disjoint_window_count) ||
      audit.disjoint_window_count !== audit.windows?.length ||
      !Number.isInteger(audit.horizon_sessions) || audit.horizon_sessions < 1) {
    throw new Error('Audit and forecast mismatch; refusing to display verdict');
  }
  const count = `${audit.overlapping_audit_count} توقعًا متداخلًا، مقابل ${audit.disjoint_window_count} فترة مستهدفة غير متداخلة`;
  if (audit.status === 'insufficient_disjoint_windows') {
    if (audit.descriptive_better_than_baseline !== null) throw new Error('Invalid insufficient-evidence verdict');
    return `فحص ${audit.horizon_sessions} جلسة: ${count}. أقل من ${audit.minimum_windows} فترات؛ لا توجد عينة كافية حتى للمقارنة الوصفية بين النموذج وخط الأساس. لا توجد نتيجة تفوق. الفترات غير المتداخلة ليست بالضرورة مستقلة إحصائيًا.`;
  }
  if (audit.status !== 'descriptive_disjoint_audit' ||
      audit.disjoint_window_count < audit.minimum_windows ||
      typeof audit.descriptive_better_than_baseline !== 'boolean') {
    throw new Error('Unsupported audit status or verdict');
  }
  const verdict = audit.descriptive_better_than_baseline ?
    'كان متوسط خطأ النموذج أقل من خط الأساس في هذه العينة فقط' :
    'لم يكن متوسط خطأ النموذج أقل من خط الأساس في هذه العينة';
  return `فحص ${audit.horizon_sessions} جلسة: ${count}. ${verdict}. المقارنة وصفية فقط؛ الفترات غير المتداخلة ليست بالضرورة مستقلة إحصائيًا، ولا تثبت قدرة مستقبلية على التنبؤ.`;
}
