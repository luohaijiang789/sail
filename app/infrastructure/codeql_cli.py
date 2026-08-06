"""CodeQL CLI 封装。

封装 database create / database analyze / database info 三类命令，
供 BUILD_CODEQL_DATABASE 与 RUN_CODEQL_VULN_SCAN 阶段使用。
数据库缓存键计算见 docs/02-build.md「CodeQL 数据库缓存」。
"""

from dataclasses import dataclass


@dataclass
class CodeQLDatabase:
    """CodeQL 数据库构建结果摘要。"""

    db_path: str
    language: str
    build_mode: str
    quality: str
    source_file_count: int
    extraction_warning_count: int


@dataclass
class DatabaseInfo:
    """``codeql database info`` 输出摘要。"""

    db_path: str
    language: str
    source_root: str
    source_file_count: int
    extraction_warning_count: int


def create_database(
    db_path: str,
    language: str,
    build_command: str,
    source_root: str,
) -> CodeQLDatabase:
    """执行 ``codeql database create``，返回构建结果摘要。

    Args:
        db_path: 数据库输出路径。
        language: 语言，如 ``java-kotlin``。
        build_command: 编译命令，如 ``./mvnw -DskipTests clean package``。
        source_root: 源码根目录。

    Returns:
        CodeQLDatabase 构建结果（含质量/文件数等）。
    """
    raise NotImplementedError


def analyze_database(db_path: str, query_pack: str, output_sarif_path: str) -> str:
    """执行 ``codeql database analyze``，产出 SARIF，返回输出路径。

    Args:
        db_path: 已构建的 CodeQL 数据库路径。
        query_pack: 查询包名，如 ``codeql/java-queries``。
        output_sarif_path: SARIF 结果输出路径。

    Returns:
        SARIF 文件路径。
    """
    raise NotImplementedError


def get_database_info(db_path: str) -> DatabaseInfo:
    """执行 ``codeql database info``，返回数据库信息摘要。"""
    raise NotImplementedError
