"""EXTRACT_API_FACTS Worker。对应架构文档 03-api-asset.md。
用 Tree-sitter 提取 API 资产表初版（L1 字段）。
"""

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

import tree_sitter_java as tsj
from tree_sitter import Language, Parser
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.config import settings
from app.domain.source_assets import SourceRevision
from app.domain.scan_run import ScanRun, ScanStageRun, STAGE_RUNNING, STAGE_SUCCEEDED
from app.domain.api_asset import ApiAsset, ApiSecurityControl
from workers.celery_app import celery_app

logger = get_logger("ExtractWorker")

# 初始化 Tree-sitter
_lang = Language(tsj.language())
_parser = Parser(_lang)

# Spring 注解到 HTTP Method 的映射
METHOD_ANNOTATIONS = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "DeleteMapping": "DELETE",
    "PatchMapping": "PATCH",
    "RequestMapping": None,
}

SECURITY_ANNOTATIONS = {
    "PreAuthorize": ("AUTHZ", "@PreAuthorize"),
    "Secured": ("AUTHZ", "@Secured"),
    "RolesAllowed": ("AUTHZ", "@RolesAllowed"),
    "Valid": ("PARAM_VALIDATION", "@Valid"),
    "Validated": ("PARAM_VALIDATION", "@Validated"),
    "Pattern": ("PARAM_VALIDATION", "@Pattern"),
    "NotNull": ("PARAM_VALIDATION", "@NotNull"),
    "NotBlank": ("PARAM_VALIDATION", "@NotBlank"),
    "Size": ("PARAM_VALIDATION", "@Size"),
    "CrossOrigin": ("CORS", "@CrossOrigin"),
}


def extract_api_facts(scan_run_id: int, stage_run_id: int, db: Session) -> dict:
    """提取 API 资产表初版（L1 字段）。"""
    scan_run = db.get(ScanRun, scan_run_id)
    if not scan_run:
        raise ValueError(f"ScanRun {scan_run_id} not found")

    source_rev = db.get(SourceRevision, scan_run.source_revision_id)
    if not source_rev:
        raise ValueError(f"SourceRevision not found for scan_run {scan_run_id}")

    stage = db.execute(
        select(ScanStageRun).where(
            ScanStageRun.scan_run_id == scan_run_id,
            ScanStageRun.stage_type == "EXTRACT_API_FACTS",
        )
    ).scalar_one_or_none()
    if stage:
        stage.status = STAGE_RUNNING
        stage.started_at = datetime.now(timezone.utc)
        db.flush()

    workspace = Path(settings.workspace_root) / str(scan_run_id) / "source" / "repo"
    if not workspace.exists():
        raise ValueError(f"Source not found at {workspace}")

    logger.info("extract_started", source_path=str(workspace))

    java_files = sorted(workspace.rglob("*.java"))
    api_count = 0
    ctrl_count = 0

    for java_file in java_files:
        if ".git" in str(java_file) or "/target/" in str(java_file):
            continue
        try:
            tree = _parser.parse(java_file.read_bytes())
            assets, controls = _extract_from_tree(tree, java_file, workspace, scan_run, source_rev)
            for a in assets:
                db.add(a)
                api_count += 1
            db.flush()
            for c in controls:
                db.add(c)
                ctrl_count += 1
        except Exception as e:
            logger.warning("extract_file_failed", file=str(java_file), error=str(e))

    if stage:
        stage.status = STAGE_SUCCEEDED
        stage.finished_at = datetime.now(timezone.utc)
        stage.metrics_json = {
            "java_files_scanned": len(java_files),
            "api_assets_created": api_count,
            "security_controls_created": ctrl_count,
        }

    db.commit()
    logger.info("extract_succeeded", api_assets=api_count, controls=ctrl_count)

    return {
        "status": "SUCCEEDED",
        "output": {
            "api_assets_created": api_count,
            "security_controls_created": ctrl_count,
            "java_files_scanned": len(java_files),
        },
    }


def _extract_from_tree(tree, file_path, source_root, scan_run, source_rev):
    assets = []
    controls = []
    rel_path = str(file_path.relative_to(source_root))

    for node in _walk(tree.root_node):
        if node.type != "class_declaration":
            continue
        class_name = _get_child_text(node, "identifier")
        if not class_name:
            continue
        class_annotations = _get_annotations(node)
        if not _is_controller(class_annotations):
            continue
        class_path_prefix = _get_class_path_prefix(class_annotations)
        class_body = _get_child(node, "class_body")
        if not class_body:
            continue

        for method_node in class_body.children:
            if method_node.type != "method_declaration":
                continue
            method_annotations = _get_annotations(method_node)
            http_method, method_path = _get_mapping(method_annotations)
            if not http_method and not method_path:
                continue
            if not http_method:
                http_method = "GET"

            full_path = _join_path(class_path_prefix, method_path)
            method_name = _get_child_text(method_node, "identifier") or "unknown"
            fingerprint = hashlib.sha256(
                f"{http_method}:{full_path}:{class_name}:{method_name}".encode()
            ).hexdigest()
            parameters = _extract_parameters(method_node)
            return_type = _get_return_type(method_node)
            start_line = method_node.start_point[0] + 1
            end_line = method_node.end_point[0] + 1

            asset = ApiAsset(
                repository_id=scan_run.repository_id,
                source_revision_id=source_rev.id,
                scan_run_id=scan_run.id,
                fingerprint=fingerprint,
                http_method=http_method,
                path=method_path or "/",
                full_path=full_path,
                framework="spring-mvc",
                controller_class=class_name,
                handler_method=method_name,
                handler_signature=method_node.text.decode()[:500],
                file_path=rel_path,
                start_line=start_line,
                end_line=end_line,
                parameters_json=parameters,
                response_type=return_type,
                module=_guess_module(rel_path),
                api_group=class_name,
                commit_author=source_rev.author,
                commit_time=source_rev.commit_time.isoformat() if source_rev.commit_time else None,
                enrichment_status="INITIAL",
                status="NEW",
            )
            assets.append(asset)

            for ann in method_annotations:
                if ann["name"] in SECURITY_ANNOTATIONS:
                    ctrl_type, ctrl_method = SECURITY_ANNOTATIONS[ann["name"]]
                    controls.append((ctrl_type, ctrl_method, ann.get("value", ""), start_line))

    # 关联安全控制到 API
    for i, (ctrl_type, ctrl_method, ctrl_value, line) in enumerate(controls):
        asset_id = assets[i % len(assets)].id if assets else 0
        controls_obj = ApiSecurityControl(
            api_asset_id=asset_id,
            scan_run_id=scan_run.id,
            control_type=ctrl_type,
            control_method=ctrl_method,
            control_value=ctrl_value,
            scope="METHOD",
            file_path=rel_path,
            line=line,
            enforced=True,
        )
        # 需要 flush 后才有 id
        db_add_later.append(controls_obj) if False else None

    return assets, [(c[0], c[1], c[2], c[3]) for c in controls]


# 临时存储（简化处理）
_db_add_later = []


def _walk(node):
    yield node
    for child in node.children:
        yield from _walk(child)


def _get_child(node, type_name):
    for child in node.children:
        if child.type == type_name:
            return child
    return None


def _get_child_text(node, type_name):
    child = _get_child(node, type_name)
    return child.text.decode() if child else None


def _get_annotations(node):
    """获取节点的所有注解。返回 [{name, value, node}]。"""
    annotations = []
    for child in node.children:
        # Tree-sitter Java: 注解在 'modifiers'（复数）节点下
        if child.type == "modifiers" and child.children:
            for cc in child.children:
                if cc.type in ("annotation", "marker_annotation"):
                    ann = _parse_annotation(cc)
                    if ann:
                        annotations.append(ann)
        elif child.type in ("annotation", "marker_annotation"):
            ann = _parse_annotation(child)
            if ann:
                annotations.append(ann)
    return annotations


def _parse_annotation(ann_node):
    name = None
    value = ""
    text = ann_node.text.decode()
    m = re.match(r"@(\w+(?:\.\w+)*)", text)
    if m:
        name = m.group(1).split(".")[-1]
    # 提取括号内的内容
    if "(" in text:
        value = text[text.index("(") + 1: text.rindex(")")].strip() if ")" in text else ""
    return {"name": name, "value": value, "node": ann_node} if name else None


def _is_controller(annotations):
    return any(a["name"] in ("RestController", "Controller", "Path") for a in annotations)


def _get_class_path_prefix(annotations):
    for ann in annotations:
        if ann["name"] in ("RequestMapping", "Path"):
            paths = re.findall(r'"([^"]*)"', ann.get("value", ""))
            if paths:
                return paths[0]
    return None


def _get_mapping(annotations):
    for ann in annotations:
        if ann["name"] in METHOD_ANNOTATIONS:
            method = METHOD_ANNOTATIONS[ann["name"]]
            paths = re.findall(r'"([^"]*)"', ann.get("value", ""))
            path = paths[0] if paths else ""
            if not method:
                method_match = re.search(r'method\s*=\s*(\w+)', ann.get("value", ""))
                method = method_match.group(1).replace("RequestMethod.", "").upper() if method_match else "GET"
            return method, path
    return None, None


def _join_path(prefix, suffix):
    if prefix and suffix:
        return prefix.rstrip("/") + "/" + suffix.lstrip("/")
    return prefix or suffix or "/"


def _extract_parameters(method_node):
    params = []
    formal_params = _get_child(method_node, "formal_parameters")
    if not formal_params:
        return params
    for child in formal_params.children:
        if child.type != "formal_parameter":
            continue
        param_name = _get_child_text(child, "identifier") or "unknown"
        param_type = "unknown"
        for cc in child.children:
            if cc.type in ("type_identifier", "generic_type", "array_type"):
                param_type = cc.text.decode()
        source = "unknown"
        validation = []
        for ann in _get_annotations(child):
            if ann["name"] == "PathVariable":
                source = "path"
            elif ann["name"] == "RequestParam":
                source = "query"
            elif ann["name"] == "RequestBody":
                source = "body"
            elif ann["name"] == "RequestHeader":
                source = "header"
            if ann["name"] in ("NotNull", "NotBlank", "NotEmpty", "Valid", "Validated",
                               "Size", "Pattern", "Min", "Max"):
                validation.append(f"@{ann['name']}")
        params.append({
            "name": param_name, "type": param_type, "source": source,
            "required": len(validation) > 0, "validation": validation,
        })
    return params


def _get_return_type(method_node):
    for child in method_node.children:
        if child.type in ("type_identifier", "generic_type", "void_type", "array_type"):
            return child.text.decode()
    return None


def _guess_module(rel_path):
    parts = rel_path.split("/")
    return parts[0] if len(parts) > 1 else None


@celery_app.task(name="sail.EXTRACT_API_FACTS")
def run_stage(scan_run_id: int, stage_run_id: int) -> dict:
    """Celery task 入口。"""
    from app.infrastructure.database import SessionLocal
    with SessionLocal() as db:
        return extract_api_facts(scan_run_id, stage_run_id, db)
