// frontend/apps/web-ele/src/utils/formatters.ts
/** commit SHA 截短（默认前 12 位）。 */
export function fmtCommit(sha: string | null | undefined, len = 12): string {
  if (!sha) return '—';
  return sha.length > len ? sha.slice(0, len) : sha;
}

/** ISO 时间 → YYYY-MM-DD HH:MM。 */
export function fmtTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  return iso.replace('T', ' ').slice(0, 16);
}

/** JSON 对象 → 摘要字符串（截断）。 */
export function fmtJson(obj: any, max = 80): string {
  if (!obj) return '—';
  const s = typeof obj === 'string' ? obj : JSON.stringify(obj);
  return s.length > max ? s.slice(0, max) + '…' : s;
}

/** metrics_json 摘要：取前 N 个 k=v 拼接。 */
export function fmtMetrics(metrics: Record<string, any> | null | undefined, n = 3): string {
  if (!metrics || typeof metrics !== 'object') return '—';
  const entries = Object.entries(metrics).slice(0, n);
  return entries.map(([k, v]) => `${k}=${typeof v === 'object' ? fmtJson(v, 30) : v}`).join(' · ');
}