import type {
  DataflowNode,
  Finding,
  FindingEvidence,
  FindingInstance,
  FindingStatusPayload,
  PageQuery,
  PageResult,
} from '#/types/sail';

import { requestClient } from '#/api/request';

export namespace FindingsApi {
  export type Query = PageQuery & {
    repositoryId?: number;
    scanRunId?: number;
    severity?: Finding['severity'];
    status?: Finding['status'];
    ruleId?: number;
    cwe?: string;
    apiAssetId?: number;
    aiVerdict?: string;
    instanceStatus?: FindingInstance['status'];
  };
}

/**
 * 漏洞列表（分页）
 */
export async function getFindingsApi(params: FindingsApi.Query) {
  return requestClient.get<PageResult<Finding>>('/findings', { params });
}

/**
 * 漏洞详情
 */
export async function getFindingApi(findingId: number) {
  return requestClient.get<Finding>(`/findings/${findingId}`);
}

/**
 * 漏洞实例列表（同一漏洞跨扫描的历史实例）
 */
export async function getFindingInstancesApi(findingId: number) {
  return requestClient.get<FindingInstance[]>(
    `/findings/${findingId}/instances`,
  );
}

/**
 * 漏洞状态变更
 */
export async function updateFindingStatusApi(
  findingId: number,
  data: FindingStatusPayload,
) {
  return requestClient.request<Finding>(`/findings/${findingId}/status`, {
    data,
    method: 'PATCH',
  });
}

/**
 * 漏洞证据
 */
export async function getFindingEvidenceApi(findingId: number) {
  return requestClient.get<FindingEvidence[]>(
    `/findings/${findingId}/evidence`,
  );
}

/**
 * 数据流（Source→CallPath→Sink）
 */
export async function getFindingDataflowApi(findingId: number) {
  return requestClient.get<DataflowNode[]>(
    `/findings/${findingId}/dataflow`,
  );
}
