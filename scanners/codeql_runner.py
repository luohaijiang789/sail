"""CodeQL 执行器：封装 CodeQL CLI 调用。

对应架构文档 05-finding-model.md 与 08-orchestration.md。提供两类执行：

1. :func:`run_vuln_scan` —— 漏洞扫描，用 rule pack 对 CodeQL 数据库跑查询，产出 SARIF。
2. :func:`run_api_enrich` —— API 信息补全查询（ADR-12/17：CodeQL 退回本职只扫漏洞，
   API 信息提取用 Tree-sitter；此处仅保留可选的深度补全查询接口）。
"""

from __future__ import annotations


def run_vuln_scan(codeql_db_path: str, rule_pack: str, output_sarif_path: str) -> str:
    """对 CodeQL 数据库执行漏洞扫描，产出 SARIF。

    Args:
        codeql_db_path: CodeQL 数据库目录绝对路径。
        rule_pack: CodeQL pack 名（对应 ``rule_pack.codeql_pack_name``），如 ``codeql/java-queries``。
        output_sarif_path: 输出 SARIF 文件绝对路径。

    Returns:
        实际产出的 SARIF 文件绝对路径（可能与入参一致）。

    Raises:
        RuntimeError: CodeQL CLI 执行失败或退出码非 0。
    """
    raise NotImplementedError


def run_api_enrich(codeql_db_path: str, enrich_queries: str, output_path: str) -> str:
    """对 CodeQL 数据库执行 API 信息补全查询，产出结构化结果。

    用于深度层（``ENRICH_API_DEPTH``）补充跨文件调用链/数据流等 L2 字段。

    Args:
        codeql_db_path: CodeQL 数据库目录绝对路径。
        enrich_queries: 补全查询 pack 或 query 路径。
        output_path: 输出文件绝对路径（SARIF 或 BQRS）。

    Returns:
        实际产出的文件绝对路径。
    """
    raise NotImplementedError
