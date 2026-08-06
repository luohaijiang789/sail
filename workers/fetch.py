"""FETCH_SOURCE Worker。对应架构文档 02-build.md「Fetch Worker」。职责：拉取仓库代码、钉到固定 commit、归档 MinIO、创建 SourceRevision。"""

from workers.celery_app import celery_app


@celery_app.task(name="sail.FETCH_SOURCE")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    """拉取源码并建立不可变 SourceRevision。

    输入：scan_run_id 关联的 Repository + revision_ref（分支/tag/commit）。
    流程：
      1. 取仓库凭证 → 2. ``git clone --depth 1``（指定 commit 则
         ``git fetch --depth 1 origin <sha>``） → 3. 解析为固定 commit_sha
      → 4. 生成 source_fingerprint → 5. 打包归档到 MinIO
         （``projects/{pid}/revisions/{sha}/source/source.tar.zst``）
      → 6. 创建 source_revision 记录。
    输出：``{"status": "SUCCEEDED", "output": {"source_artifact_id": <int>,
    "commit_sha": <str>, "source_revision_id": <int>}}``。
    on_failure=ABORT：失败直接终止整个 ScanRun。
    """
    raise NotImplementedError
