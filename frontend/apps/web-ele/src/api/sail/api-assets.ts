import type {
  ApiAsset,
  ApiCheck,
  CallEdge,
  PageQuery,
  PageResult,
  ResourceAccess,
  SecurityControl,
} from '#/types/sail';

import { requestClient } from '#/api/request';

export namespace ApiAssetsApi {
  export type Query = PageQuery & {
    repository_id?: number;
    scan_run_id?: number;
    http_method?: string;
    status?: ApiAsset['status'];
    security_level?: string;
    min_security_score?: number;
    has_findings?: boolean;
  };

  export type VersionHistoryItem = {
    scanRunId: number;
    commitSha: string;
    commitTime: string;
    securityScore: number;
    securityLevel: string;
    changeType: 'CHANGED' | 'NEW' | 'REMOVED' | 'UNCHANGED';
    changes?: Record<string, any>;
  };

  export type ApiDiff = {
    added: ApiAsset[];
    removed: ApiAsset[];
    changed: ApiAsset[];
  };
}

/**
 * API 资产列表（分页）
 */
export async function getApiAssetsApi(params: ApiAssetsApi.Query) {
  return requestClient.get<PageResult<ApiAsset>>('/api-assets', { params });
}

/**
 * API 资产详情
 */
export async function getApiAssetApi(assetId: number) {
  return requestClient.get<ApiAsset>(`/api-assets/${assetId}`);
}

/**
 * 调用链树（call-tree）
 */
export async function getCallTreeApi(assetId: number) {
  return requestClient.get<CallEdge[]>(`/api-assets/${assetId}/call-tree`);
}

/**
 * 资源访问
 */
export async function getResourcesApi(assetId: number) {
  return requestClient.get<ResourceAccess[]>(
    `/api-assets/${assetId}/resources`,
  );
}

/**
 * 安全控制
 */
export async function getSecurityControlsApi(assetId: number) {
  return requestClient.get<SecurityControl[]>(
    `/api-assets/${assetId}/security`,
  );
}

/**
 * check 矩阵
 */
export async function getApiChecksApi(assetId: number) {
  return requestClient.get<ApiCheck[]>(`/api-assets/${assetId}/checks`);
}

/**
 * 该 API 的漏洞
 */
export async function getApiAssetFindingsApi(
  assetId: number,
  params?: PageQuery,
) {
  return requestClient.get<any[]>(
    `/api-assets/${assetId}/findings`,
    { params },
  );
}

/**
 * 版本历史
 */
export async function getApiAssetHistoryApi(assetId: number) {
  return requestClient.get<ApiAssetsApi.VersionHistoryItem[]>(
    `/api-assets/${assetId}/history`,
  );
}

/**
 * 安全画像 + 安全控制（详情页汇总用）
 *
 * 后端 `GET /api-assets/{id}/security` 一次返回 `{profile, controls}`。
 */
export async function getApiAssetSecurityApi(assetId: number) {
  return requestClient.get<{ profile: any | null; controls: any[] }>(
    `/api-assets/${assetId}/security`,
  );
}
