import type { FeedbackPayload } from '#/types/sail';

import { requestClient } from '#/api/request';

export namespace FeedbackApi {
  export type Result = {
    id: number;
    suggestionStatus: 'APPLIED' | 'APPROVED' | 'PENDING' | 'REJECTED';
    improvementType?: 'NO_CHANGE' | 'PATTERN' | 'PROMPT' | 'RULE';
  };
}

/**
 * 提交 check 反馈（04-check-and-security.md 自动优化反馈闭环）
 */
export async function submitCheckFeedbackApi(
  assetId: number,
  checkId: number,
  data: FeedbackPayload,
) {
  return requestClient.post<FeedbackApi.Result>(
    `/api-assets/${assetId}/checks/${checkId}/feedback`,
    data,
  );
}
