"""PREFLIGHT Worker。对应架构文档 02-build.md「BuildPlan」。职责：预检源码、生成 BuildPlan、识别 JDK 与构建工具。"""

from workers.celery_app import celery_app


@celery_app.task(name="sail.PREFLIGHT")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    """预检源码并产出 BuildPlan。

    输入：source_artifact_id（FETCH_SOURCE 产物）。
    流程：按优先级确定构建信息——项目配置 > sail.yaml > 自动识别 > 默认；
    识别 jdk_version、build_tool（maven/gradle/...）、build_tool_version、
    build_command；决定 build_mode（有命令 MANUAL_BUILD，无命令 AUTOBUILD）。
    识别结果持久化到 source_revision.detected_build_plan（ADR-08，同 commit 复用）。
    输出：``{"status": "SUCCEEDED", "output": {"build_plan": {...},
    "build_plan_hash": <str>}}``。
    on_failure=ABORT。
    """
    raise NotImplementedError
