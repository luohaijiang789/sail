"""SAIL 平台统一异常体系。

所有业务异常继承 SailError，携带 error_code 供 Worker 回调使用。
"""

from typing import Any


class SailError(Exception):
    """SAIL 平台异常基类。"""

    error_code: str = "SAIL_ERROR"
    retryable: bool = False
    http_status: int = 500

    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(message)
        self.message = message
        self.context = context

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "retryable": self.retryable,
            "context": self.context,
        }


# === 源码资产层异常 ===

class FetchError(SailError):
    error_code = "FETCH_ERROR"
    http_status = 500


class RepositoryNotFoundError(FetchError):
    error_code = "REPOSITORY_NOT_FOUND"
    http_status = 404


class AuthenticationFailedError(FetchError):
    error_code = "AUTHENTICATION_FAILED"
    http_status = 401


class BranchNotFoundError(FetchError):
    error_code = "BRANCH_NOT_FOUND"
    http_status = 404


class CommitNotFoundError(FetchError):
    error_code = "COMMIT_NOT_FOUND"
    http_status = 404


class CloneTimeoutError(FetchError):
    error_code = "CLONE_TIMEOUT"
    retryable = True


class RepositoryTooLargeError(FetchError):
    error_code = "REPOSITORY_TOO_LARGE"


# === 构建异常 ===

class BuildError(SailError):
    error_code = "BUILD_ERROR"


class BuildScriptError(BuildError):
    """构建脚本本身有错，不可重试。"""
    error_code = "BUILD_SCRIPT_ERROR"


class JdkIncompatibleError(BuildError):
    error_code = "JDK_INCOMPATIBLE"
    retryable = False


class BuildTimeoutError(BuildError):
    error_code = "BUILD_TIMEOUT"
    retryable = True


class OutOfMemoryError(BuildError):
    error_code = "OUT_OF_MEMORY"
    retryable = True


class DiskLimitExceededError(BuildError):
    error_code = "DISK_LIMIT_EXCEEDED"
    retryable = True


# === CodeQL 异常 ===

class CodeQLError(SailError):
    error_code = "CODEQL_ERROR"


class CodeQLSyntaxError(CodeQLError):
    """QL 查询语法错误，不可重试。"""
    error_code = "QL_SYNTAX_ERROR"
    retryable = False


class CodeQLDatabaseNotFoundError(CodeQLError):
    error_code = "CODEQL_DB_NOT_FOUND"
    http_status = 404


# === AI 异常 ===

class AiError(SailError):
    error_code = "AI_ERROR"


class LlmRateLimitError(AiError):
    error_code = "LLM_RATE_LIMIT"
    retryable = True


class LlmTimeoutError(AiError):
    error_code = "LLM_TIMEOUT"
    retryable = True


class EvidenceBundleIncompleteError(AiError):
    error_code = "EVIDENCE_INCOMPLETE"


# === 编排异常 ===

class OrchestratorError(SailError):
    error_code = "ORCHESTRATOR_ERROR"


class StageNotReadyError(OrchestratorError):
    """阶段的上游未完成。"""
    error_code = "STAGE_NOT_READY"
    http_status = 409


class ScanRunNotFoundError(OrchestratorError):
    error_code = "SCAN_RUN_NOT_FOUND"
    http_status = 404


class ScanRunCancelledError(OrchestratorError):
    error_code = "SCAN_RUN_CANCELLED"
    http_status = 409


# === 资源未找到 ===

class ApiAssetNotFoundError(SailError):
    """API 资产不存在。"""
    error_code = "API_ASSET_NOT_FOUND"
    http_status = 404


class FindingNotFoundError(SailError):
    """漏洞不存在。"""
    error_code = "FINDING_NOT_FOUND"
    http_status = 404


# === 基础设施异常 ===

class InfrastructureError(SailError):
    error_code = "INFRASTRUCTURE_ERROR"


class DatabaseError(InfrastructureError):
    error_code = "DB_TRANSIENT"
    retryable = True


class ObjectStorageError(InfrastructureError):
    error_code = "OBJECT_STORAGE_ERROR"
    retryable = True


class RedisError(InfrastructureError):
    error_code = "REDIS_ERROR"
    retryable = True


# === 配置异常 ===

class ConfigError(SailError):
    error_code = "CONFIG_PARSE_ERROR"
    retryable = False


class ValidationError(SailError):
    error_code = "VALIDATION_ERROR"
    http_status = 422


# === 可重试错误分类 ===

RETRYABLE_ERROR_CODES: frozenset[str] = frozenset({
    "CLONE_TIMEOUT",
    "BUILD_TIMEOUT",
    "OUT_OF_MEMORY",
    "DISK_LIMIT_EXCEEDED",
    "LLM_RATE_LIMIT",
    "LLM_TIMEOUT",
    "DB_TRANSIENT",
    "OBJECT_STORAGE_ERROR",
    "REDIS_ERROR",
    "NETWORK_ERROR",
})

# 资源错误分类
RESOURCE_ERROR_CODES: frozenset[str] = frozenset({
    "OUT_OF_MEMORY",
    "DISK_LIMIT_EXCEEDED",
    "BUILD_TIMEOUT",
    "CLONE_TIMEOUT",
})

# 不可重试错误分类
NON_RETRYABLE_ERROR_CODES: frozenset[str] = frozenset({
    "REPOSITORY_NOT_FOUND",
    "AUTHENTICATION_FAILED",
    "BRANCH_NOT_FOUND",
    "COMMIT_NOT_FOUND",
    "BUILD_SCRIPT_ERROR",
    "JDK_INCOMPATIBLE",
    "QL_SYNTAX_ERROR",
    "CONFIG_PARSE_ERROR",
    "REPOSITORY_TOO_LARGE",
})


def classify_error(error_code: str) -> str:
    """分类错误码：RETRYABLE / NON_RETRYABLE / RESOURCE。"""
    if error_code in RESOURCE_ERROR_CODES:
        return "RESOURCE"
    if error_code in RETRYABLE_ERROR_CODES:
        return "RETRYABLE"
    if error_code in NON_RETRYABLE_ERROR_CODES:
        return "NON_RETRYABLE"
    return "UNKNOWN"
