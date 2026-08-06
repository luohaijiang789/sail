"""BUILD_CODEQL_DATABASE Worker。对应架构文档 02-build.md「CodeQL 包裹编译」「三种构建模式」。职责：用 CodeQL 包裹编译过程建库，支持三种模式。"""

from workers.celery_app import celery_app


@celery_app.task(name="sail.BUILD_CODEQL_DATABASE")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    """CodeQL 包裹编译并构建代码数据库。

    输入：commit_sha + build_plan_hash。
    流程：CodeQL 直接包裹编译命令建库（``codeql database create
    --command=...``），禁止先完整编译再让 CodeQL 重编（D2）。三种模式：
    MANUAL_BUILD（有 build_command）/ AUTOBUILD（无命令默认）/ NO_BUILD
    （``--build-mode=none``，二者都失败后降级，只取语法，须裁剪数据流类规则）。
    数据库质量分级：FULL_MANUAL_BUILD / SUCCESSFUL_AUTOBUILD / PARTIAL_BUILD /
    NO_BUILD_DEGRADED / BUILD_FAILED。按
    ``sha256(repo_id+commit_sha+build_plan_hash+codeql_cli+extractor)`` 缓存
    （不含 rule_pack_version，规则升级复用同一数据库）。
    输出：``{"status": "SUCCEEDED", "output": {"codeql_db_id": <int>,
    "build_mode": <str>, "db_quality": <str>}}``；NO_BUILD 时降级标记。
    on_failure=DEGRADE：降级到 NO_BUILD 而非直接失败。
    """
    raise NotImplementedError
