import type {
  PageQuery,
  PageResult,
  Repository,
  RepositoryPayload,
} from '#/types/sail';

import { requestClient } from '#/api/request';

export namespace RepositoriesApi {
  export type Query = PageQuery & {
    repository_type?: string;
    last_scan_status?: string;
  };

  export type ValidateResult = {
    ok: boolean;
    branch?: string;
    commitSha?: string;
    errorMessage?: string;
  };
}

/**
 * 仓库列表（分页）
 */
export async function getRepositoriesApi(params: RepositoriesApi.Query) {
  return requestClient.get<PageResult<Repository>>('/repositories', { params });
}

/**
 * 仓库详情
 */
export async function getRepositoryApi(id: number) {
  return requestClient.get<Repository>(`/repositories/${id}`);
}

/**
 * 创建仓库
 */
export async function createRepositoryApi(data: RepositoryPayload) {
  return requestClient.post<Repository>('/repositories', data);
}

/**
 * 更新仓库
 */
export async function updateRepositoryApi(
  id: number,
  data: Partial<RepositoryPayload>,
) {
  return requestClient.request<Repository>(`/repositories/${id}`, {
    data,
    method: 'PATCH',
  });
}

/**
 * 校验仓库凭证与可达性
 */
export async function validateRepositoryApi(id: number) {
  return requestClient.post<RepositoriesApi.ValidateResult>(
    `/repositories/${id}/validate`,
  );
}
