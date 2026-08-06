"""CodeQL 执行器：封装 CodeQL CLI 调用。

提供 run_vuln_scan（漏洞扫描产出 SARIF）与 run_api_enrich（可选深度补全）。
CodeQL 不可用时由调用方降级到 taint_analyzer。
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from app.config import settings
from app.core.exceptions import CodeQLError
from app.core.logging import get_logger

logger = get_logger("CodeQLRunner")


def is_codeql_available() -> bool:
    """CodeQL CLI 是否可用（PATH 或配置的 codeql_cli_path）。"""
    cli = settings.codeql_cli_path
    if cli and cli != "codeql" and Path(cli).exists():
        return True
    return shutil.which("codeql") is not None


def codeql_executable() -> str:
    cli = settings.codeql_cli_path
    if cli and cli != "codeql" and Path(cli).exists():
        return cli
    return "codeql"


def run_vuln_scan(codeql_db_path: str, rule_pack: str, output_sarif_path: str) -> str:
    """对 CodeQL 数据库执行漏洞扫描，产出 SARIF。

    Args:
        codeql_db_path: CodeQL 数据库目录。
        rule_pack: CodeQL pack 名，如 codeql/java-queries。
        output_sarif_path: 输出 SARIF 绝对路径。

    Returns:
        实际产出的 SARIF 文件绝对路径。

    Raises:
        CodeQLError: CodeQL CLI 执行失败。
    """
    if not is_codeql_available():
        raise CodeQLError("CodeQL CLI not available")

    cli = codeql_executable()
    Path(output_sarif_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        cli, "database", "analyze",
        codeql_db_path,
        "--format=sarif-latest",
        f"--output={output_sarif_path}",
        "--threads=0",
    ]
    # rule_pack 形如 codeql/java-queries:codeql-suites/java-security-and-quality.qls
    if ":" in rule_pack:
        pack, suite = rule_pack.split(":", 1)
        cmd += [pack, suite]
    else:
        cmd += [rule_pack]

    logger.info("codeql_analyze_start", db=codeql_db_path, rule_pack=rule_pack)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0:
        raise CodeQLError(
            f"CodeQL analyze failed (rc={result.returncode}): {result.stderr[:500]}"
        )
    logger.info("codeql_analyze_done", sarif=output_sarif_path)
    return output_sarif_path


def run_api_enrich(codeql_db_path: str, enrich_queries: str, output_path: str) -> str:
    """对 CodeQL 数据库执行 API 信息补全查询。阶段一未使用。"""
    raise NotImplementedError


def create_database(source_root: str, db_path: str, build_command: str | None = None,
                    language: str = "java", overwrite: bool = True) -> str:
    """构建 CodeQL 数据库。

    Args:
        source_root: 源码根目录。
        db_path: 数据库输出目录。
        build_command: 构建命令；None 时用 autobuild。
        language: 语言。

    Returns:
        数据库目录绝对路径。

    Raises:
        CodeQLError: 构建失败。
    """
    if not is_codeql_available():
        raise CodeQLError("CodeQL CLI not available")

    cli = codeql_executable()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [cli, "database", "create", db_path, f"--language={language}",
           f"--source-root={source_root}", "--overwrite"]
    if build_command:
        cmd.append(f"--command={build_command}")
    else:
        cmd.append("--no-overwrite") if False else None
        # autobuild：不传 --command，让 CodeQL 自行推断
        if not build_command:
            cmd = [cli, "database", "create", db_path, f"--language={language}",
                   f"--source-root={source_root}", "--overwrite"]

    logger.info("codeql_db_create_start", source=source_root, build_command=build_command)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if result.returncode != 0:
        raise CodeQLError(
            f"CodeQL database create failed (rc={result.returncode}): {result.stderr[:800]}"
        )
    logger.info("codeql_db_create_done", db=db_path)
    return db_path
