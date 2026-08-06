# 02. 源码拉取与编译

> [← 01-data-flow](01-data-flow.md)　|　下一章：[03-api-asset](03-api-asset.md)

## 核心对象

```
project: id, name, owner, default_scan_profile_id
repository: id, project_id, name, git_url, default_branch, credential_id, repository_type, last_scanned_commit
source_revision: id, repository_id, commit_sha, branch, tag, commit_time, author,
                 source_artifact_id, source_fingerprint, detected_build_plan
artifact: id, project_id, scan_run_id, artifact_type, storage_key, size_bytes, checksum, retention_policy
```

**SourceRevision 是核心**（D1）：用户选分支，扫描必须钉到 commit_sha。`detected_build_plan` 存预检识别的构建信息，同一 commit 永远用同一份 plan，保证缓存 hash 稳定。

## Fetch Worker

1. 获取仓库凭证 → 2. 浅克隆 → 3. 解析为固定 commit_sha → 4. 生成 source_fingerprint → 5. 归档到 MinIO → 6. 创建 source_revision

优先 `git clone --depth 1`；指定 commit 用 `git fetch --depth 1 origin <sha>`。

异常分类：可重试（网络/存储）、不可重试（仓库不存在/认证失败）、资源（超时/过大）。

## BuildPlan

PREFLIGHT 阶段生成。来源优先级：项目配置 > sail.yaml > 自动识别 > 默认。

```json
{
  "jdk_version": "17", "build_tool": "maven", "build_tool_version": "3.9",
  "build_command": ["./mvnw", "-DskipTests", "clean", "package"],
  "timeout_seconds": 3600, "memory_limit_mb": 12288, "build_mode": "MANUAL"
}
```

**自动识别结果持久化到 source_revision**（ADR-08），后续复用不重新识别。

## CodeQL 的定位（ADR-17）

CodeQL 只做两件事：① 漏洞扫描（source-sink，核心）；② 可选深度语义查询。**不提取 API 信息**——太重。

## 三种构建模式（ADR-07）

```
BuildPlan 有 build_command？
  是 → MANUAL_BUILD
  否 → AUTOBUILD
二者都失败 → NO_BUILD 降级
```

AUTOBUILD 不是 MANUAL 的降级——是"无命令时的默认"。真正降级只到 NO_BUILD。

## CodeQL 包裹编译（D2）

```bash
codeql database create /workspace/codeql-db \
  --language=java-kotlin \
  --command="./mvnw -DskipTests clean package" \
  --source-root=/workspace/source
```

禁止先完整编译一次再让 CodeQL 重新编译。

## NO_BUILD 模式与规则裁剪

NO_BUILD（`--build-mode=none`）只提取语法，丢失类型解析和数据流。必须裁剪规则：

| 规则类别 | NO_BUILD 下 |
|---|---|
| 数据流类（SQL注入/XSS/SSRF/路径遍历） | 失效，跳过 |
| 类型继承类（反序列化） | 失效，跳过 |
| 语法类（硬编码密码/弱加密/空catch） | 可用 |
| 配置类（debug模式/不安全cookie） | 可用 |

数据库质量：`FULL_MANUAL_BUILD / SUCCESSFUL_AUTOBUILD / PARTIAL_BUILD / NO_BUILD_DEGRADED / BUILD_FAILED`

## CodeQL 数据库缓存

```
cache_key = sha256(repository_id + commit_sha + build_plan_hash + codeql_cli_version + extractor_version)
```

不含 rule_pack_version——规则升级时复用同一数据库，只重新跑查询。

## 对象存储路径

```
projects/{project_id}/revisions/{commit_sha}/source/source.tar.zst
projects/{project_id}/revisions/{commit_sha}/codeql/{cache_key}/database.tar.zst
scans/{scan_run_id}/logs/build.log
scans/{scan_run_id}/results/{rule_pack}.sarif
```
