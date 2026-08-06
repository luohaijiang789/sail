"""check 表 + 安全画像模型。对应架构文档 04-check-and-security.md。"""

from sqlalchemy import JSON, BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain import Base, TimestampMixin

# check 结果六态
CHECK_PASS = "PASS"
CHECK_LOW = "LOW"
CHECK_MEDIUM = "MEDIUM"
CHECK_HIGH = "HIGH"
CHECK_CRITICAL = "CRITICAL"
CHECK_NOT_CHECKED = "NOT_CHECKED"


class ApiCheck(Base, TimestampMixin):
    __tablename__ = "api_check"

    id: Mapped[int] = mapped_column(Integer().with_variant(BigInteger, "mysql"), primary_key=True, autoincrement=True)
    api_asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("api_asset.id"), nullable=False, index=True)
    scan_run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("scan_run.id"), nullable=False)
    source_revision_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("source_revision.id"), nullable=False)
    check_item_key: Mapped[str] = mapped_column(String(50), nullable=False)  # SQL_INJECTION/XSS/NO_AUTHN/...
    check_item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    check_category: Mapped[str] = mapped_column(String(30), nullable=False)  # INJECTION/ACCESS_CONTROL/...
    check_source: Mapped[str] = mapped_column(String(20), nullable=False)  # CODEQL/API_ASSET/MIXED
    result: Mapped[str] = mapped_column(String(20), nullable=False)  # PASS/LOW/MEDIUM/HIGH/CRITICAL/NOT_CHECKED
    finding_candidate_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("finding_candidate.id"))
    evidence_summary: Mapped[str | None] = mapped_column(Text)
    detail_json: Mapped[dict | None] = mapped_column(JSON)


class ApiSecurityProfile(Base, TimestampMixin):
    __tablename__ = "api_security_profile"

    id: Mapped[int] = mapped_column(Integer().with_variant(BigInteger, "mysql"), primary_key=True, autoincrement=True)
    api_asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("api_asset.id"), nullable=False, index=True)
    scan_run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("scan_run.id"), nullable=False)
    source_revision_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("source_revision.id"), nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-100，分高=危险
    overall_level: Mapped[str] = mapped_column(String(20), nullable=False)  # SAFE/LOW_RISK/.../CRITICAL
    exposure_score: Mapped[int] = mapped_column(Integer, nullable=False)
    callchain_score: Mapped[int] = mapped_column(Integer, nullable=False)
    data_sensitivity_score: Mapped[int] = mapped_column(Integer, nullable=False)
    codequality_score: Mapped[int] = mapped_column(Integer, nullable=False)
    check_coverage: Mapped[int] = mapped_column(Integer, default=0)  # 已检查项数/总项数 * 100
    blind_spots: Mapped[list | None] = mapped_column(JSON)  # NOT_CHECKED 的检查项列表
    risk_factors_json: Mapped[dict | None] = mapped_column(JSON)
    ai_assessment: Mapped[dict | None] = mapped_column(JSON)


# 预定义必查清单（对应 04-check-and-security.md）
PREDEFINED_CHECK_ITEMS: list[dict[str, str]] = [
    # 注入类（CodeQL 判定）
    {"key": "SQL_INJECTION", "name": "SQL 注入", "category": "INJECTION", "source": "CODEQL"},
    {"key": "COMMAND_INJECTION", "name": "命令注入", "category": "INJECTION", "source": "CODEQL"},
    {"key": "XPATH_INJECTION", "name": "XPath 注入", "category": "INJECTION", "source": "CODEQL"},
    {"key": "LDAP_INJECTION", "name": "LDAP 注入", "category": "INJECTION", "source": "CODEQL"},
    # 客户端类（CodeQL 判定）
    {"key": "XSS", "name": "XSS", "category": "CLIENT", "source": "CODEQL"},
    {"key": "OPEN_REDIRECT", "name": "开放重定向", "category": "CLIENT", "source": "CODEQL"},
    # 服务端类（CodeQL 判定）
    {"key": "DESERIALIZATION", "name": "反序列化", "category": "SERVER", "source": "CODEQL"},
    {"key": "SSRF", "name": "SSRF", "category": "SERVER", "source": "CODEQL"},
    {"key": "PATH_TRAVERSAL", "name": "路径遍历", "category": "SERVER", "source": "CODEQL"},
    # 访问控制类（API 资产判定）
    {"key": "NO_AUTHN", "name": "鉴权缺失", "category": "ACCESS_CONTROL", "source": "API_ASSET"},
    {"key": "NO_AUTHZ", "name": "授权不足", "category": "ACCESS_CONTROL", "source": "API_ASSET"},
    {"key": "NO_PARAM_VALIDATION", "name": "参数校验缺失", "category": "ACCESS_CONTROL", "source": "API_ASSET"},
    {"key": "NO_CSRF", "name": "CSRF 缺失", "category": "ACCESS_CONTROL", "source": "API_ASSET"},
    {"key": "NO_RATE_LIMIT", "name": "限流缺失", "category": "ACCESS_CONTROL", "source": "API_ASSET"},
    # 数据保护类（API 资产判定）
    {"key": "SENSITIVE_DATA_RETURN", "name": "敏感数据返回", "category": "DATA_PROTECTION", "source": "API_ASSET"},
    {"key": "SENSITIVE_DATA_ACCESS", "name": "敏感数据访问", "category": "DATA_PROTECTION", "source": "API_ASSET"},
    # 代码质量类（CodeQL 判定）
    {"key": "HARDCODED_CREDENTIALS", "name": "硬编码凭证", "category": "CODE_QUALITY", "source": "CODEQL"},
    {"key": "WEAK_CRYPTO", "name": "弱加密", "category": "CODE_QUALITY", "source": "CODEQL"},
    {"key": "EMPTY_CATCH", "name": "空 catch", "category": "CODE_QUALITY", "source": "CODEQL"},
    {"key": "INSECURE_RANDOM", "name": "不安全随机数", "category": "CODE_QUALITY", "source": "CODEQL"},
]

# 四维度权重
DIMENSION_WEIGHTS = {
    "exposure": 0.30,
    "callchain": 0.35,
    "data_sensitivity": 0.20,
    "codequality": 0.15,
}

# 结果 → 分值映射
RESULT_SCORE_MAP = {
    CHECK_CRITICAL: 100,
    CHECK_HIGH: 80,
    CHECK_MEDIUM: 60,
    CHECK_LOW: 40,
    CHECK_PASS: 0,
    CHECK_NOT_CHECKED: 0,
}

# 维度 → 包含的检查项
DIMENSION_CHECK_ITEMS = {
    "exposure": ["NO_AUTHN", "NO_AUTHZ", "NO_PARAM_VALIDATION", "NO_CSRF", "NO_RATE_LIMIT"],
    "callchain": ["SQL_INJECTION", "COMMAND_INJECTION", "DESERIALIZATION", "SSRF", "PATH_TRAVERSAL",
                  "XPATH_INJECTION", "LDAP_INJECTION", "OPEN_REDIRECT"],
    "data_sensitivity": ["SENSITIVE_DATA_RETURN", "SENSITIVE_DATA_ACCESS"],
    "codequality": ["HARDCODED_CREDENTIALS", "WEAK_CRYPTO", "EMPTY_CATCH", "INSECURE_RANDOM"],
}
