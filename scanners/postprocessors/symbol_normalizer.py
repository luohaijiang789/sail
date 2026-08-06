"""符号标准化后处理器与归一化算法。

对应架构文档 05-finding-model.md「指纹与归一化算法（D6 / ADR-09）」。提供三个归一化
函数供后处理器与指纹计算复用，并提供 :class:`SymbolNormalizer` 后处理器把这些归一化
结果回填到 :class:`FindingCandidateData` 的 ``symbol``、``source_location``、
``sink_location``、``dataflow_path`` 字段。

归一化算法（不变性：重命名变量/调整空格/移动位置 → 指纹不变；修改数据流路径上的方法调用 → 指纹变）：

- :func:`normalize_symbol`：去参数名/局部变量名，保留完全限定类名 + 方法名 + 参数**类型**序列。
- :func:`normalize_dataflow_signature`：取路径上每节点的方法签名，``;`` 分隔。
- :func:`normalize_path`：POSIX 相对路径，去 ``./``。
"""

from __future__ import annotations

from scanners.postprocessors.base import BasePostprocessor, register_postprocessor
from scanners.sarif_parser import FindingCandidateData


def normalize_symbol(symbol: str | None) -> str:
    """归一化 Java 符号：去参数名/局部变量名，保留完全限定类名 + 方法名 + 参数类型序列。

    输入形如 ``com.acme.UserController.getUser(String name, Long id)``，
    归一化为 ``com.acme.UserController.getUser(String,Long)``。处理步骤：
    1. ``None`` / 空串 → 空串。
    2. 去除空白与换行。
    3. 提取 ``类全限定名.方法名(参数类型序列)``，丢弃参数名与形参默认值。
    4. 参数类型序列去泛型实参（``List<User>`` → ``List``），保留数组维度。
    5. 返回不带空格的规范形式。

    Args:
        symbol: 原始符号字符串，可能含参数名/泛型/空白。

    Returns:
        归一化后的符号字符串；输入为空返回 ``""``。
    """
    raise NotImplementedError


def normalize_dataflow_signature(dataflow_path: list[dict]) -> str:
    """归一化数据流路径签名：取路径上每节点的方法签名，``;`` 分隔。

    每个节点是 ``{"file":..., "line":..., "symbol":..., "signature":...}`` dict。
    取每节点的 ``signature``（若无则取 ``symbol``）经 :func:`normalize_symbol` 归一化，
    用 ``;`` 拼接成单个字符串。节点顺序保持原 dataflow_path 顺序。

    Args:
        dataflow_path: 数据流路径节点列表（见 :attr:`FindingCandidateData.dataflow_path`）。

    Returns:
        ``;`` 分隔的归一化签名串；空列表返回 ``""``。
    """
    raise NotImplementedError


def normalize_path(file_path: str | None) -> str:
    """归一化文件路径为 POSIX 相对路径，去 ``./`` 前缀，保留模块前缀。

    处理步骤：
    1. ``None`` → ``""``。
    2. Windows 路径分隔符 ``\\`` → ``/``。
    3. 去除开头的 ``./`` 与重复的 ``.`` 段。
    4. 保留模块前缀（如 ``modules/user-service/src/...``）。
    5. 不做绝对路径到相对路径的根裁剪（调用方需保证已是仓库内相对路径，
       或由本函数按 ``source_root`` 裁剪——当前实现仅做分隔符与前缀归一化）。

    Args:
        file_path: 原始文件路径。

    Returns:
        POSIX 相对路径字符串；输入为空返回 ``""``。
    """
    raise NotImplementedError


@register_postprocessor
class SymbolNormalizer(BasePostprocessor):
    """符号标准化后处理器。

    把 :func:`normalize_symbol` / :func:`normalize_dataflow_signature` 的结果回填到
    候选数据的 ``symbol``、``source_location["symbol"]``、``sink_location["symbol"]``
    以及 ``dataflow_path[*]["signature"]`` 字段，使后续指纹计算可直接读取已归一化值。

    注意：本后处理器只做归一化回填，不改路径字段（路径归一化由
    :class:`~scanners.postprocessors.path_normalizer.PathNormalizer` 负责）。
    """

    name = "symbol_normalizer"

    def process(self, candidates: list[FindingCandidateData]) -> list[FindingCandidateData]:
        """对候选列表做符号归一化回填。

        Args:
            candidates: SARIF 解析产出的候选列表。

        Returns:
            符号归一化后的候选列表（新列表，候选对象为副本，不修改入参）。
        """
        raise NotImplementedError

    @staticmethod
    def _normalize_location(location: dict) -> dict:
        """归一化单个 location dict 的 ``symbol`` 字段，返回副本。"""
        raise NotImplementedError
