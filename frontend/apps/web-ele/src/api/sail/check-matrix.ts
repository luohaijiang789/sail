import { requestClient } from '#/api/request';

export interface CheckMatrixData {
  apis: { id: number; name: string }[];
  checks: { key: string; name: string; category: string }[];
  cells: Record<number, Record<string, string>>;
}

export async function getCheckMatrixApi(scanRunId: number) {
  return requestClient.get<CheckMatrixData>('/check-matrix', {
    params: { scan_run_id: scanRunId },
  });
}
