// frontend/apps/web-ele/src/utils/status-colors.ts
/** 状态/严重度/等级 → Element Plus ElTag type 统一配色。所有页面共用。 */
export type TagType = 'danger' | 'info' | 'primary' | 'success' | 'warning';

const MAP: Record<string, TagType> = {
  // 扫描/阶段状态
  SUCCEEDED: 'success',
  RUNNING: 'warning',
  FAILED: 'danger',
  PARTIAL_SUCCEEDED: 'info',
  CANCELLED: 'info',
  CREATED: 'info',
  QUEUED: 'info',
  PENDING: 'info',
  SKIPPED: 'info',
  // 严重度
  CRITICAL: 'danger',
  HIGH: 'danger',
  MEDIUM: 'warning',
  LOW: 'info',
  INFO: 'info',
  // check 结果
  PASS: 'success',
  NOT_CHECKED: 'info',
  // 安全等级
  SAFE: 'success',
  LOW_RISK: 'success',
  MEDIUM_RISK: 'warning',
  HIGH_RISK: 'danger',
  CRITICAL: 'danger',
  // 仓库状态
  ACTIVE: 'success',
  // AI verdict
  TRUE_POSITIVE: 'danger',
  LIKELY_TRUE_POSITIVE: 'danger',
  UNCERTAIN: 'warning',
  LIKELY_FALSE_POSITIVE: 'info',
  FALSE_POSITIVE: 'info',
  NEED_MORE_CONTEXT: 'warning',
  INSUFFICIENT_CONTEXT: 'info',
  // 漏洞状态
  OPEN: 'danger',
  FIXED: 'success',
  REAPPEARED: 'warning',
  FALSE_POSITIVE: 'info',
};

export function statusTagType(value: string | null | undefined): TagType {
  if (!value) return 'info';
  return MAP[value] ?? 'info';
}

/** 安全分 0-100 → 颜色类（用于单元格背景/文字色） */
export function scoreColor(score: number): string {
  if (score >= 70) return 'text-red-500';
  if (score >= 50) return 'text-orange-500';
  if (score >= 25) return 'text-yellow-600';
  return 'text-green-500';
}