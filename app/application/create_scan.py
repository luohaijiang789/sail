"""创建扫描的应用服务。

负责：解析 revision 引用 → 查询/创建 SourceRevision → 创建 ScanRun 记录
→ 按 STAGE_DEFINITIONS 批量创建所有 ScanStageRun → 提交首个 Celery 任务。
"""

from app.domain.scan_run import ScanRun


def create_scan(
    repository_id: int,
    revision: str,
    scan_profile_id: int | None,
    ai_analysis: bool,
) -> ScanRun:
    """创建一次扫描并派发。

    Args:
        repository_id: 仓库 ID。
        revision: 版本引用（分支名/Tag/commit_sha），由调用方解析。
        scan_profile_id: 扫描配置 ID，可为空走默认。
        ai_analysis: 是否开启 AI 分析阶段（影响可选阶段是否实际执行）。

    Returns:
        新建的 ScanRun 记录（含所有 ScanStageRun）。
    """
    raise NotImplementedError
