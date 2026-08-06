"""基于 Tree-sitter 的轻量污点分析器（CodeQL 不可用时的降级扫描器）。

真实静态分析，不依赖编译：对每个 Controller handler 做过程内污点追踪——
识别用户可控 source（@RequestParam/@PathVariable/@RequestBody/getParameter 等），
经局部变量传播，追踪到危险 sink（SQL 执行、Runtime.exec、ProcessBuilder、
文件路径、XPath/LDAP 求值、响应回写），产出 FindingCandidateData。

这是 CodeQL 的降级替代：覆盖面更窄（过程内、无类型推断），但产出真实 source→sink 链路。
明确标注 scanner_id="sail-taint"，与真 CodeQL（scanner_id="codeql"）区分。
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import tree_sitter_java as tsj
from tree_sitter import Language, Parser

from scanners.sarif_parser import FindingCandidateData

_lang = Language(tsj.language())
_parser = Parser(_lang)

# 用户输入 source：注解 或 标准取值 API
SOURCE_ANNOTATIONS = {"RequestParam", "PathVariable", "RequestBody", "RequestHeader", "QueryParam", "FormParam"}
SOURCE_METHODS = {
    "getParameter", "getParameterValues", "getHeader", "getCookie", "getQueryString",
    "getRequestURI", "getPathInfo", "getRemoteUser", "getAttributes",
}

# sink → 规则映射。method 名（调用）→ (rule_id, severity, category, cwe)
SINK_RULES = {
    # SQL 注入
    "executeQuery": ("sql-injection", "HIGH", "INJECTION", "CWE-89"),
    "executeUpdate": ("sql-injection", "HIGH", "INJECTION", "CWE-89"),
    "execute": ("sql-injection", "HIGH", "INJECTION", "CWE-89"),
    "executeLargeUpdate": ("sql-injection", "HIGH", "INJECTION", "CWE-89"),
    "createNativeQuery": ("sql-injection", "HIGH", "INJECTION", "CWE-89"),
    "createQuery": ("sql-injection", "HIGH", "INJECTION", "CWE-89"),
    "prepareStatement": ("sql-injection", "MEDIUM", "INJECTION", "CWE-89"),
    # 命令注入
    "exec": ("command-injection", "HIGH", "INJECTION", "CWE-78"),
    "start": ("command-injection", "MEDIUM", "INJECTION", "CWE-78"),
    # 路径遍历
    # new File(...) / Paths.get(...) 单独在 sink 检测里处理
    # XPath
    "evaluate": ("xpath-injection", "MEDIUM", "INJECTION", "CWE-643"),
    # LDAP
    "search": ("ldap-injection", "MEDIUM", "INJECTION", "CWE-90"),
    # 响应回写（XSS）
    "write": ("xss", "MEDIUM", "CLIENT_SIDE", "CWE-79"),
    "println": ("xss", "LOW", "CLIENT_SIDE", "CWE-79"),
}

# 构造器 sink：new Xxx(tainted) → 规则
CONSTRUCTOR_SINKS = {
    "File": ("path-traversal", "MEDIUM", "PATH_MANIPULATION", "CWE-22"),
    "FileInputStream": ("path-traversal", "MEDIUM", "PATH_MANIPULATION", "CWE-22"),
    "FileOutputStream": ("path-traversal", "MEDIUM", "PATH_MANIPULATION", "CWE-22"),
    "ProcessBuilder": ("command-injection", "HIGH", "INJECTION", "CWE-78"),
}

# 安全 SQL 模式：prepareStatement + setXxx（参数化）。若 sink 调用前可见 setString/setInt，降级。
SAFE_PARAM_SETTERS = {"setString", "setInt", "setLong", "setDouble", "setFloat", "setObject", "setBytes", "setBoolean", "setDate", "setTimestamp", "setShort", "setByte"}


@dataclass
class _TaintState:
    """过程内污点状态：tainted 局部变量名集合 + source 位置记录。"""
    tainted_vars: set[str] = field(default_factory=set)
    var_source_loc: dict[str, dict] = field(default_factory=dict)


def analyze_repository(source_root: Path) -> list[FindingCandidateData]:
    """扫描整个仓库，返回所有污点流候选。"""
    candidates: list[FindingCandidateData] = []
    java_files = sorted(p for p in source_root.rglob("*.java")
                        if ".git" not in str(p) and "/target/" not in str(p))
    for java_file in java_files:
        try:
            tree = _parser.parse(java_file.read_bytes())
            candidates.extend(_analyze_tree(tree, java_file, source_root))
        except Exception:
            continue
    return candidates


def _analyze_tree(tree, file_path: Path, source_root: Path) -> list[FindingCandidateData]:
    """分析单个文件的 AST，找 controller handler 内的污点流。"""
    out: list[FindingCandidateData] = []
    rel = str(file_path.relative_to(source_root))

    for node in _walk(tree.root_node):
        if node.type != "method_declaration":
            continue
        # 只分析带 mapping 注解的 handler（source 起点）
        annotations = _get_annotations(node)
        if not _is_handler(annotations):
            continue
        method_name = _get_child_text(node, "identifier") or "unknown"
        state = _TaintState()
        # 初始化 source：带 source 注解的形参
        _seed_param_sources(node, annotations, state)
        # 遍历方法体做传播 + sink 检测
        body = _get_child(node, "block") or _get_child(node, "method_body")
        if body:
            _analyze_block(body, state, rel, method_name, out)
    return out


def _analyze_block(block_node, state: _TaintState, rel: str, method: str, out: list) -> None:
    """遍历块语句，做赋值传播与 sink 检测。"""
    for node in _walk(block_node):
        # 赋值传播：local_variable_declaration / assignment_expression
        if node.type == "local_variable_declaration":
            _handle_decl(node, state)
        elif node.type == "assignment_expression":
            _handle_assign(node, state)
        # sink 检测：方法调用 / 对象创建
        elif node.type == "method_invocation":
            _check_method_sink(node, state, rel, method, out)
        elif node.type == "object_creation_expression":
            _check_constructor_sink(node, state, rel, method, out)


def _handle_decl(node, state: _TaintState) -> None:
    """local_variable_declaration：Type name = init; 若 init 引用 tainted 或 source，则 name tainted。"""
    name = _decl_var_name(node)
    if not name:
        return
    init = _get_child(node, "init" ) or _find_init(node)
    if init is None:
        return
    # 取值调用 source？
    invoked = _invoked_method_name(init)
    if invoked in SOURCE_METHODS:
        state.tainted_vars.add(name)
        state.var_source_loc[name] = {"line": node.start_point[0] + 1, "symbol": invoked}
        return
    # 引用已 tainted 变量？
    refs = _ident_refs(init)
    if refs & state.tainted_vars:
        state.tainted_vars.add(name)
        src = next(iter(refs & state.tainted_vars))
        state.var_source_loc[name] = state.var_source_loc.get(src, {"line": node.start_point[0] + 1})


def _handle_assign(node, state: _TaintState) -> None:
    """assignment_expression：lhs = rhs; 传播 taint。"""
    lhs = _get_child_text(node, "identifier")
    if not lhs:
        return
    rhs = None
    for c in node.children:
        if c.type not in ("identifier", "=") and c.type != "identifier":
            rhs = c
            break
    if rhs is None:
        # 取等号右侧
        parts = node.text.decode().split("=", 1)
        if len(parts) == 2:
            rhs_text = parts[1].strip()
            if any(v in rhs_text for v in state.tainted_vars):
                state.tainted_vars.add(lhs)
        return
    invoked = _invoked_method_name(rhs)
    if invoked in SOURCE_METHODS:
        state.tainted_vars.add(lhs)
        state.var_source_loc[lhs] = {"line": node.start_point[0] + 1, "symbol": invoked}
        return
    refs = _ident_refs(rhs)
    if refs & state.tainted_vars:
        state.tainted_vars.add(lhs)
        src = next(iter(refs & state.tainted_vars))
        state.var_source_loc[lhs] = state.var_source_loc.get(src, {"line": node.start_point[0] + 1})


def _check_method_sink(node, state: _TaintState, rel: str, method: str, out: list) -> None:
    """方法调用：是否是 sink 且实参 tainted。"""
    invoked = _invoked_method_name(node)
    if not invoked:
        return
    # source 取值：记录但不报
    if invoked in SOURCE_METHODS:
        return
    rule = SINK_RULES.get(invoked)
    if not rule:
        return
    # XSS write：需上下文是 response.getWriter()，简化为只要参数 tainted 即报
    arg_nodes = _call_args(node)
    if not arg_nodes:
        return
    tainted_arg = None
    for arg in arg_nodes:
        refs = _ident_refs(arg)
        if refs & state.tainted_vars:
            tainted_arg = next(iter(refs & state.tainted_vars))
            break
        # 字符串拼接里含 tainted：文本里出现 tainted 变量名
        arg_text = arg.text.decode()
        if any(v in arg_text for v in state.tainted_vars):
            tainted_arg = next(v for v in state.tainted_vars if v in arg_text)
            break
    if not tainted_arg:
        return
    # 安全模式：prepareStatement 后跟 setXxx（参数化），不报
    if invoked == "prepareStatement":
        # ponytail: 粗判——若同行/邻近有 setXxx 调用，视为参数化，跳过
        # 过程内简化：prepareStatement 本身不是注入点，真正的 sink 是后续 executeQuery。
        # 这里降级：prepareStatement 不直接产出 finding。
        return
    rule_id, severity, category, cwe = rule
    src_loc = state.var_source_loc.get(tainted_arg, {"line": node.start_point[0] + 1, "symbol": tainted_arg})
    out.append(_make_candidate(
        rule_id=rule_id, severity=severity, category=category, cwe=cwe,
        rel=rel, method=method, sink_node=node, sink_method=invoked,
        source_var=tainted_arg, src_loc=src_loc,
    ))


def _check_constructor_sink(node, state: _TaintState, rel: str, method: str, out: list) -> None:
    """new Xxx(tainted)：构造器 sink。"""
    type_node = _get_child(node, "type_identifier")
    if not type_node:
        return
    type_name = type_node.text.decode()
    rule = CONSTRUCTOR_SINKS.get(type_name)
    if not rule:
        return
    arg_nodes = _call_args(node)
    if not arg_nodes:
        return
    tainted_arg = None
    for arg in arg_nodes:
        refs = _ident_refs(arg)
        if refs & state.tainted_vars:
            tainted_arg = next(iter(refs & state.tainted_vars))
            break
        arg_text = arg.text.decode()
        if any(v in arg_text for v in state.tainted_vars):
            tainted_arg = next(v for v in state.tainted_vars if v in arg_text)
            break
    if not tainted_arg:
        return
    rule_id, severity, category, cwe = rule
    src_loc = state.var_source_loc.get(tainted_arg, {"line": node.start_point[0] + 1, "symbol": tainted_arg})
    out.append(_make_candidate(
        rule_id=rule_id, severity=severity, category=category, cwe=cwe,
        rel=rel, method=method, sink_node=node, sink_method=f"new {type_name}",
        source_var=tainted_arg, src_loc=src_loc,
    ))


def _make_candidate(rule_id, severity, category, cwe, rel, method, sink_node, sink_method,
                    source_var, src_loc) -> FindingCandidateData:
    sink_line = sink_node.start_point[0] + 1
    symbol = f"{rel}::{method}"
    fp = hashlib.sha256(f"{rule_id}:{rel}:{sink_line}:{method}:{source_var}".encode()).hexdigest()[:16]
    return FindingCandidateData(
        rule_id=rule_id,
        severity=severity,
        file_path=rel,
        start_line=sink_line,
        end_line=sink_node.end_point[0] + 1,
        symbol=symbol,
        source_location={"file": rel, "line": src_loc.get("line", sink_line), "symbol": source_var},
        sink_location={"file": rel, "line": sink_line, "symbol": sink_method},
        dataflow_path=[
            {"step": 0, "file": rel, "line": src_loc.get("line", sink_line), "desc": f"source: {source_var}"},
            {"step": 1, "file": rel, "line": sink_line, "desc": f"sink: {sink_method}({source_var})"},
        ],
    )


# === AST 辅助 ===

def _walk(node):
    yield node
    for c in node.children:
        yield from _walk(c)


def _get_child(node, type_name):
    for c in node.children:
        if c.type == type_name:
            return c
    return None


def _get_child_text(node, type_name):
    c = _get_child(node, type_name)
    return c.text.decode() if c else None


def _get_annotations(node):
    anns = []
    for c in node.children:
        if c.type == "modifiers":
            for cc in c.children:
                if cc.type in ("annotation", "marker_annotation"):
                    text = cc.text.decode()
                    m = re.match(r"@(\w+)", text)
                    if m:
                        anns.append(m.group(1))
        elif c.type in ("annotation", "marker_annotation"):
            text = c.text.decode()
            m = re.match(r"@(\w+)", text)
            if m:
                anns.append(m.group(1))
    return anns


def _is_handler(annotations) -> bool:
    return any(a in ("GetMapping", "PostMapping", "PutMapping", "DeleteMapping",
                     "PatchMapping", "RequestMapping") for a in annotations)


def _seed_param_sources(node, annotations, state: _TaintState) -> None:
    """带 source 注解的形参 → taint 该形参名。"""
    params = _get_child(node, "formal_parameters")
    if not params:
        return
    for c in params.children:
        if c.type != "formal_parameter":
            continue
        param_anns = _get_annotations(c)
        name = _get_child_text(c, "identifier")
        if name and any(a in SOURCE_ANNOTATIONS for a in param_anns):
            state.tainted_vars.add(name)
            state.var_source_loc[name] = {"line": c.start_point[0] + 1, "symbol": f"@{param_anns[-1]}"}


def _decl_var_name(node) -> str | None:
    """local_variable_declaration 的变量名。"""
    for c in node.children:
        if c.type == "variable_declarator":
            name = _get_child_text(c, "identifier")
            if name:
                return name
    return None


def _find_init(node):
    """找声明里的初始化表达式。"""
    for c in node.children:
        if c.type == "variable_declarator":
            for cc in c.children:
                if cc.type not in ("identifier", "=") and cc.type != "identifier":
                    return cc
    return None


def _invoked_method_name(call_node) -> str | None:
    """方法调用的被调名。method_invocation: obj.method(args) → method；foo(args) → foo。"""
    # Tree-sitter java: 方法名是 name 节点
    name = _get_child_text(call_node, "identifier" )
    if name:
        return name
    # 形如 .execute(...) 时 identifier 在 children 里
    for c in call_node.children:
        if c.type == "identifier":
            return c.text.decode()
    return None


def _call_args(call_node) -> list:
    """方法调用的实参节点列表。"""
    args = _get_child(call_node, "argument_list")
    if not args:
        return []
    return [c for c in args.children if c.type == "argument_list" or c.type not in ("(", ")", ",", "comment") and c.type != ","]


def _ident_refs(node) -> set[str]:
    """收集节点里出现的所有 identifier 文本（粗略：变量引用）。"""
    refs = set()
    if node is None:
        return refs
    for n in _walk(node):
        if n.type == "identifier":
            refs.add(n.text.decode())
    return refs
