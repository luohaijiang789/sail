// frontend/apps/web-ele/src/components/sail-pro-table/types.ts
/** 列定义。tag 字段设为 true 时用 statusTagType 着色；formatter 自定义格式化。 */
export interface SailColumn {
  prop: string;
  label: string;
  width?: number | string;
  minWidth?: number | string;
  sortable?: boolean;
  tag?: boolean;             // 用 statusTagType(row[prop]) 渲染 ElTag
  formatter?: (row: any) => string;
  fixed?: 'left' | 'right';
  showOverflowTooltip?: boolean;
}

/** 筛选项定义。 */
export interface SailFilter {
  type: 'keyword' | 'select' | 'numberRange';
  field: string;             // 对应查询参数名（keyword 时为 'keyword'）
  label: string;
  placeholder?: string;
  options?: { label: string; value: string | number }[];  // select 用
  multiple?: boolean;        // select 是否多选
}

/** fetcher：接收查询参数，返回 { items, total }。 */
export type SailFetcher = (params: Record<string, any>) => Promise<{ items: any[]; total: number }>;
