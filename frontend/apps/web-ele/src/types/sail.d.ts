/**
 * SAIL 扫描平台前端类型定义
 *
 * 对齐架构文档：
 *  - 02-build.md (Repository / SourceRevision)
 *  - 03-api-asset.md (ApiAsset / CallEdge / ResourceAccess / SecurityControl)
 *  - 04-check-and-security.md (ApiCheck / SecurityProfile)
 *  - 05-finding-model.md (Finding / FindingInstance / AiReview)
 *  - 06-ai-analysis.md (AiReview verdict 字段)
 *  - 08-orchestration.md (ScanRun / ScanStageRun 状态机)
 */

// ============ 通用枚举 ============

/** ScanRun 状态机（ADR-03） */
export type ScanRunStatus =
  | 'CANCELLED'
  | 'CREATED'
  | 'FAILED'
  | 'PARTIAL_SUCCEEDED'
  | 'QUEUED'
  | 'RUNNING'
  | 'SUCCEEDED';

/** ScanStageRun 阶段状态 */
export type StageStatus =
  | 'CANCELLED'
  | 'FAILED_FINAL'
  | 'FAILED_RETRYABLE'
  | 'PENDING'
  | 'RUNNING'
  | 'SKIPPED'
  | 'SUCCEEDED'
  | 'TIMEOUT';

/** 阶段类型 */
export type StageType =
  | 'AI_ANALYZE'
  | 'ASSESS_API_SECURITY'
  | 'ASSEMBLE_CONTEXT'
  | 'BUILD_CODEQL_DATABASE'
  | 'ENRICH_API_DEPTH'
  | 'EXTRACT_API_FACTS'
  | 'FINALIZE'
  | 'FINDING_CANDIDATES'
  | 'FETCH_SOURCE'
  | 'MERGE_FINDINGS'
  | 'PERSIST_RESULTS'
  | 'PREFLIGHT'
  | 'RUN_CODEQL_VULN_SCAN';

/** 阶段失败策略 */
export type OnFailure = 'ABORT' | 'CONTINUE' | 'DEGRADE';

/** HTTP 方法 */
export type HttpMethod =
  | 'CONNECT'
  | 'DELETE'
  | 'GET'
  | 'HEAD'
  | 'OPTIONS'
  | 'PATCH'
  | 'POST'
  | 'PUT'
  | 'TRACE';

/** API 资产富化状态 */
export type EnrichmentStatus = 'ENRICHED' | 'FAILED' | 'INITIAL';

/** API 资产状态（跨版本） */
export type ApiAssetStatus = 'ACTIVE' | 'CHANGED' | 'REMOVED';

/** 资源类型 */
export type ResourceType =
  | 'CACHE'
  | 'DB_TABLE'
  | 'FILE_READ'
  | 'FILE_WRITE'
  | 'HTTP_OUTBOUND'
  | 'QUEUE'
  | 'RPC'
  | 'SQL_QUERY';

/** 资源操作 */
export type ResourceOperation = 'DELETE' | 'EXECUTE' | 'READ' | 'WRITE';

/** 安全控制类型 */
export type SecurityControlType =
  | 'AUTHN'
  | 'AUTHZ'
  | 'CORS'
  | 'CSRF'
  | 'INPUT_SANITIZATION'
  | 'PARAM_VALIDATION'
  | 'RATE_LIMIT';

/** 安全控制作用域 */
export type SecurityControlScope =
  | 'ENDPOINT'
  | 'GLOBAL'
  | 'METHOD'
  | 'PARAM';

/** check 结果六态 */
export type CheckResult =
  | 'CRITICAL'
  | 'HIGH'
  | 'LOW'
  | 'MEDIUM'
  | 'NOT_CHECKED'
  | 'PASS';

/** check 来源 */
export type CheckSource = 'API_ASSET' | 'CODEQL' | 'MIXED';

/** 安全等级 */
export type SecurityLevel =
  | 'CRITICAL'
  | 'HIGH_RISK'
  | 'LOW_RISK'
  | 'MEDIUM_RISK'
  | 'SAFE';

/** Finding 状态 */
export type FindingStatus =
  | 'FALSE_POSITIVE'
  | 'FIXED'
  | 'OPEN'
  | 'REAPPEARED';

/** FindingInstance 状态 */
export type FindingInstanceStatus =
  | 'NEW'
  | 'REAPPEARED'
  | 'RECURRING'
  | 'RESOLVED';

/** 漏洞严重度 */
export type Severity =
  | 'CRITICAL'
  | 'HIGH'
  | 'INFO'
  | 'LOW'
  | 'MEDIUM';

/** AI Review verdict（06-ai-analysis.md） */
export type AiVerdict =
  | 'FALSE_POSITIVE'
  | 'INSUFFICIENT_CONTEXT'
  | 'LIKELY_FALSE_POSITIVE'
  | 'LIKELY_TRUE_POSITIVE'
  | 'NEED_MORE_CONTEXT'
  | 'TRUE_POSITIVE'
  | 'UNCERTAIN';

/** AI 可利用性 */
export type Exploitability = 'HIGH' | 'LOW' | 'MEDIUM' | 'NONE';

// ============ 模型类型 ============

/** 仓库（02-build.md repository 表） */
export interface Repository {
  id: number;
  projectId: number;
  name: string;
  gitUrl: string;
  defaultBranch: string;
  credentialId: null | number;
  repositoryType: string;
  lastScannedCommit: null | string;
  // 前端展示用冗余字段
  lastScanStatus?: ScanRunStatus;
  lastScanAt?: null | string;
  apiAssetCount?: number;
  highRiskCount?: number;
  createdAt: string;
}

/** 源码版本（02-build.md source_revision 表） */
export interface SourceRevision {
  id: number;
  repositoryId: number;
  commitSha: string;
  branch: null | string;
  tag: null | string;
  commitTime: string;
  author: string;
  detectedBuildPlan: null | Record<string, any>;
}

/** 扫描运行（08-orchestration.md ScanRun） */
export interface ScanRun {
  id: number;
  repositoryId: number;
  repositoryName?: string;
  sourceRevisionId: number;
  scanProfileId: number;
  status: ScanRunStatus;
  aiAnalysis: boolean;
  startedAt: null | string;
  finishedAt: null | string;
  cancelRequested?: boolean;
  // 前端展示用冗余字段
  highRiskCount?: number;
  apiAssetCount?: number;
  findingCount?: number;
  triggeredBy?: string;
  errorMessage?: null | string;
}

/** 扫描阶段运行（08-orchestration.md scan_stage_run） */
export interface ScanStageRun {
  id: number;
  scanRunId: number;
  stageType: StageType;
  status: StageStatus;
  attempt: number;
  maxAttempts: number;
  required: boolean;
  onFailure: OnFailure;
  celeryTaskId: null | string;
  inputFingerprint: null | string;
  outputArtifactId: null | number;
  startedAt: null | string;
  finishedAt: null | string;
  heartbeatAt: null | string;
  retryable: boolean;
  errorCode: null | string;
  errorMessage: null | string;
  metricsJson?: null | Record<string, any>;
}

/** API 参数（03-api-asset.md parameters_json 元素） */
export interface ApiParameter {
  name: string;
  type: string;
  source: 'body' | 'cookie' | 'header' | 'path' | 'query';
  required: boolean;
  validation: string[];
}

/** API 资产（03-api-asset.md api_asset 主表） */
export interface ApiAsset {
  id: number;
  repositoryId: number;
  sourceRevisionId: number;
  scanRunId: number;
  fingerprint: string;
  httpMethod: HttpMethod;
  path: string;
  fullPath: string;
  framework: string;
  controllerClass: string;
  handlerMethod: string;
  handlerSignature: string;
  filePath: string;
  startLine: number;
  endLine: number;
  consumes: null | string;
  produces: null | string;
  responseType: null | string;
  parameters: ApiParameter[];
  module: null | string;
  apiGroup: null | string;
  commitAuthor: null | string;
  commitTime: null | string;
  callChainDepth: null | number;
  enrichmentStatus: EnrichmentStatus;
  firstSeenScanId: null | number;
  lastSeenScanId: null | number;
  status: ApiAssetStatus;
  createdAt: string;
  // 前端展示用冗余字段
  findingCount?: number;
  securityScore?: null | number;
  securityLevel?: null | SecurityLevel;
  checkCoverage?: null | number;
}

/** 调用链边（03-api-asset.md api_call_edge） */
export interface CallEdge {
  id: number;
  apiAssetId: number;
  scanRunId: number;
  depth: number;
  callerSymbol: string;
  callerFile: string;
  callerLine: number;
  calleeSymbol: string;
  calleeFile: string;
  calleeLine: number;
  calleeType: 'INTERNAL' | 'LIBRARY' | 'UNKNOWN';
  edgeKind: 'DIRECT_CALL' | 'LAMBDA' | 'REFLECTION' | 'VIRTUAL_DISPATCH';
  parentEdgeId: null | number;
  pathSignature: string;
}

/** 资源访问（03-api-asset.md api_resource_access） */
export interface ResourceAccess {
  id: number;
  apiAssetId: number;
  callEdgeId: null | number;
  scanRunId: number;
  sourceLayer: 'L1_DECLARED' | 'L2_CALLCHAIN';
  resourceType: ResourceType;
  resourceName: string;
  operation: ResourceOperation;
  detailJson: null | Record<string, any>;
  filePath: string;
  line: number;
  isSensitive: boolean;
}

/** 安全控制（03-api-asset.md api_security_control） */
export interface SecurityControl {
  id: number;
  apiAssetId: number;
  scanRunId: number;
  controlType: SecurityControlType;
  controlMethod: string;
  controlValue: null | string;
  scope: SecurityControlScope;
  filePath: null | string;
  line: null | number;
  enforced: boolean;
}

/** check 矩阵项（04-check-and-security.md api_check） */
export interface ApiCheck {
  id: number;
  apiAssetId: number;
  scanRunId: number;
  sourceRevisionId: number;
  checkItemKey: string;
  checkItemName: string;
  checkCategory: string;
  checkSource: CheckSource;
  result: CheckResult;
  findingCandidateId: null | number;
  evidenceSummary: null | string;
  detailJson: null | Record<string, any>;
  checkedAt: string;
}

/** 安全画像（04-check-and-security.md api_security_profile） */
export interface SecurityProfile {
  id: number;
  apiAssetId: number;
  scanRunId: number;
  overallScore: number;
  overallLevel: SecurityLevel;
  exposureScore: number;
  callchainScore: number;
  dataSensitivityScore: number;
  codequalityScore: number;
  checkCoverage: number;
  blindSpots: string[];
  riskFactorsJson: null | Record<string, any>;
  aiAssessment: null | string;
  assessedAt: string;
}

/** AI Review（06-ai-analysis.md ai_review） */
export interface AiReview {
  id: number;
  candidateId: number;
  apiAssetId: null | number;
  modelProvider: string;
  modelName: string;
  promptVersion: string;
  evidenceHash: string;
  round: number;
  verdict: AiVerdict;
  confidence: number;
  exploitability: Exploitability;
  authRequired: boolean;
  authEnforced: boolean;
  reachableFromEndpoint: boolean;
  responseJson: null | Record<string, any>;
  needRequestsJson: null | Record<string, any>[];
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  durationSeconds: number;
  status: string;
}

/** 漏洞（05-finding-model.md finding） */
export interface Finding {
  id: number;
  repositoryId: number;
  fingerprint: string;
  ruleId: number;
  ruleName?: string;
  ruleKey?: string;
  cwe?: null | string;
  severity: Severity;
  status: FindingStatus;
  firstSeenScanId: number;
  lastSeenScanId: number;
  firstSeenCommit: string;
  lastSeenCommit: string;
  apiAssetId: null | number;
  title: string;
  description: string;
  remediation: null | string;
  createdAt: string;
  // 前端展示用冗余字段
  repositoryName?: string;
  apiAssetLabel?: null | string;
  aiVerdict?: null | AiVerdict;
  aiConfidence?: null | number;
  riskScore?: null | number;
  instanceStatus?: FindingInstanceStatus;
}

/** 漏洞实例（05-finding-model.md finding_instance） */
export interface FindingInstance {
  id: number;
  findingId: number;
  scanRunId: number;
  sourceRevisionId: number;
  candidateId: number;
  filePath: string;
  startLine: number;
  endLine: number;
  symbol: string;
  apiAssetId: null | number;
  rawSeverity: Severity;
  finalSeverity: Severity;
  aiVerdict: AiVerdict;
  aiConfidence: number;
  riskScore: number;
  status: FindingInstanceStatus;
}

/** 数据流路径节点（漏洞详情 Source→CallPath→Sink） */
export interface DataflowNode {
  step: number;
  kind: 'CALL_PATH' | 'SINK' | 'SOURCE';
  symbol: string;
  filePath: string;
  line: number;
  snippet: null | string;
  description: null | string;
}

/** 漏洞证据 */
export interface FindingEvidence {
  file: string;
  lines: string;
  description: string;
}

// ============ 请求载荷 ============

/** 创建扫描载荷（09-api-frontend.md） */
export interface ScanCreatePayload {
  repositoryId: number;
  revision: {
    type: 'branch' | 'commit' | 'tag';
    value: string;
  };
  scanProfileId: number;
  aiAnalysis: boolean;
}

/** 仓库创建/更新载荷 */
export interface RepositoryPayload {
  name: string;
  gitUrl: string;
  defaultBranch: string;
  credentialId: null | number;
  repositoryType: string;
  projectId?: number;
}

/** 漏洞状态变更载荷 */
export interface FindingStatusPayload {
  status: FindingStatus;
  reason?: string;
}

/** check 反馈载荷（04-check-and-security.md feedback_analysis） */
export interface FeedbackPayload {
  humanVerdict: 'CONFIRMED' | 'FALSE_POSITIVE' | 'UNCERTAIN';
  humanReason: string;
  improvementType?: 'NO_CHANGE' | 'PATTERN' | 'PROMPT' | 'RULE';
}

// ============ 列表查询通用 ============

/** 分页查询参数（对齐后端 snake_case：page / page_size） */
export interface PageQuery {
  page: number;
  page_size: number;
  keyword?: string;
  [key: string]: any;
}

/** 分页返回结构（对齐后端 snake_case） */
export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

/** SSE 事件（09-api-frontend.md /api/scans/{id}/events） */
export interface ScanSseEvent {
  eventSeq: number;
  eventType: 'LOG' | 'STAGE_FINISHED' | 'STAGE_STARTED' | 'SCAN_FINISHED';
  payload: Record<string, any>;
  timestamp: string;
}

/** 日志行 */
export interface ScanLogLine {
  seq: number;
  timestamp: string;
  level: 'DEBUG' | 'ERROR' | 'INFO' | 'WARN';
  stage?: StageType;
  message: string;
}
