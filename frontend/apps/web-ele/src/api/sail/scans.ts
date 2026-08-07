import type {
  PageQuery,
  PageResult,
  ScanCreatePayload,
  ScanLogLine,
  ScanRun,
  ScanSseEvent,
  ScanStageRun,
} from '#/types/sail';

import { requestClient } from '#/api/request';

export namespace ScansApi {
  export type Query = PageQuery & {
    repository_id?: number;
    status?: ScanRun['status'];
  };

  export type Stats = {
    total_scans: number;
    running_scans: number;
    succeeded_scans: number;
    total_findings: number;
    high_risk_findings: number;
    total_repositories: number;
    total_api_assets: number;
    recent_scans: ScanRun[];
  };
}

/**
 * 扫描列表（分页）
 */
export async function getScansApi(params: ScansApi.Query) {
  return requestClient.get<PageResult<ScanRun>>('/scans', { params });
}

/**
 * 扫描详情
 */
export async function getScanApi(scanId: number) {
  return requestClient.get<ScanRun>(`/scans/${scanId}`);
}

/**
 * 创建扫描
 */
export async function createScanApi(data: ScanCreatePayload) {
  // 后端期望 snake_case，前端用 camelCase，在此映射
  return requestClient.post<ScanRun>('/scans', {
    repository_id: data.repositoryId,
    revision: data.revision,
    scan_profile_id: data.scanProfileId,
    ai_analysis: data.aiAnalysis,
  });
}

/**
 * 取消扫描
 */
export async function cancelScanApi(scanId: number) {
  return requestClient.post<ScanRun>(`/scans/${scanId}/cancel`);
}

/**
 * 重试整个扫描
 */
export async function retryScanApi(scanId: number) {
  return requestClient.post<ScanRun>(`/scans/${scanId}/retry`);
}

/**
 * 重试单个阶段
 */
export async function retryStageApi(scanId: number, stageId: number) {
  return requestClient.post<ScanStageRun>(
    `/scans/${scanId}/stages/${stageId}/retry`,
  );
}

/**
 * 扫描阶段列表（时间线）
 */
export async function getScanStagesApi(scanId: number) {
  return requestClient.get<ScanStageRun[]>(`/scans/${scanId}/stages`);
}

/**
 * 流式日志（分页拉取，与 SSE 互补）
 */
export async function getScanLogsApi(
  scanId: number,
  params?: { seq?: number; limit?: number },
) {
  return requestClient.get<ScanLogLine[]>(`/scans/${scanId}/logs`, { params });
}

/**
 * 扫描下 API 资产列表
 */
export async function getScanApiAssetsApi(
  scanId: number,
  params?: PageQuery,
) {
  return requestClient.get<PageResult<any>>(`/scans/${scanId}/api-assets`, {
    params,
  });
}

/**
 * 扫描 API 变化对比
 */
export async function getScanApiDiffApi(scanId: number) {
  return requestClient.get<Record<string, any>>(
    `/scans/${scanId}/api-diff`,
  );
}

/**
 * 概览统计
 */
export async function getScanStatsApi() {
  return requestClient.get<ScansApi.Stats>('/scans/stats');
}

/**
 * SSE 订阅扫描事件
 *
 * 返回一个 EventSource，事件带 event_seq，重连带 Last-Event-ID（ADR-10）。
 * 注意：EventSource 由浏览器原生提供，不走 requestClient。
 */
export function subscribeScanEventsApi(
  scanId: number,
  onEvent: (event: ScanSseEvent) => void,
  onError?: (error: Event) => void,
): EventSource {
  const url = `/scans/${scanId}/events`;
  const es = new EventSource(url);
  es.addEventListener('message', (msg: MessageEvent) => {
    try {
      const parsed = JSON.parse(msg.data) as ScanSseEvent;
      onEvent(parsed);
    } catch {
      // 忽略非 JSON 心跳消息
    }
  });
  es.addEventListener('error', (error: Event) => {
    onError?.(error);
  });
  return es;
}
