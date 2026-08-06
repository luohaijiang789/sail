# 10. 基础设施与部署

> [← 09-api-frontend](09-api-frontend.md)　|　下一章：[11-roadmap](11-roadmap.md)

## Celery 队列

```
source_fetch / source_extract / java_build_jdk17 / codeql_query / ai_analysis / result_process / maintenance
```

## 并发估算（单机 32C/64GB 示例）

| 队列 | 并发 | 依据 |
|---|---|---|
| source_fetch | 8 | IO密集，~500MB/任务 |
| source_extract | 4 | CPU密集，4C/任务 |
| java_build | 2 | 峰值16GB+8C/任务 |
| codeql_query | 3 | 4C+4GB/任务 |
| ai_analysis | 16 | 调LLM API，几乎不耗本地 |
| result_process | 4 | CPU+DB |

公式：`并发 = min(可用CPU/单任务CPU, 可用内存/单任务内存)`

## 日志

每条日志结构化：`level, event, scan_run_id, stage_run_id, task_id, repository_id, commit_sha, worker`

### 构建日志流式上传

工作区构建结束销毁（安全要求），日志必须流式上传 MinIO：

```
构建输出 → tee本地 + 实时tail上传MinIO → 构建结束本地销毁 → MinIO保留
```

## 可观测指标

扫描成功率、拉取失败率、构建成功率（按mode分维度）、CodeQL DB缓存命中率、平均构建时长、AI分析成功率、AI平均token/成本、单仓扫描成本、Worker排队时间。

Flower 看 Celery 任务级；业务监控读 MySQL 的 ScanRun/ScanStageRun。

## 构建环境隔离

Maven/Gradle 构建会执行仓库中的代码和插件，必须隔离：

```
非root用户 / 独立临时工作区 / CPU+内存+磁盘+进程数限制 / 超时
禁止访问宿主机目录 / 禁止Docker Socket / 默认禁止公司内网
只开放依赖源 / 构建结束销毁工作区（日志已流式上传）
```

## Worker 权限最小化

| Worker | 有 | 无 |
|---|---|---|
| Fetch | Git凭证、MinIO写 | DB管理员、AI密钥 |
| Build | 源码读、依赖源、MinIO写 | 用户管理、AI密钥 |
| AI | LLM密钥、Evidence读 | 源码访问、DB管理员 |
| Postprocess | DB写、MinIO读 | Git凭证、AI密钥 |

## Docker Compose

```
public-network:    nginx / frontend / api
internal-network:  api / workers / mysql / redis / minio
```

MySQL/Redis/MinIO 不对公网开放。容器间用服务名访问，不硬编码 IP。
