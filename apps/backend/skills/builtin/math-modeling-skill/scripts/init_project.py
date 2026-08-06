"""数学建模项目初始化脚本。

创建标准目录结构和初始状态文件 modeling/index.json。
支持重复执行，不覆盖用户已有内容。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]  # noqa: F401

# 项目目录规范
_DIR_LAYOUT = [
    "statement",
    "data/raw",
    "data/processed",
    "analysis",
    "research/notes",
    "model",
    "src",
    "configs",
    "runs",
    "validation",
    "results/figures",
    "results/tables",
    "paper/sections",
    "paper/latex",
    "paper/build",
    "audit",
    "modeling",
]

# 占位文件标记（用于检测模板内容）
_PLACEHOLDER_MARKERS = [
    "[在此粘贴赛题内容]",
    "[记录格式、篇幅、截止时间等]",
    "[记录假设、限制、工具规则等]",
    "[待填写]",
]

# 占位文件（相对路径 -> 内容）
_PLACEHOLDER_FILES = {
    "statement/problem.md": "# 赛题原文\n\n[在此粘贴赛题内容]",
    "statement/requirements.md": "# 提交要求\n\n[记录格式、篇幅、截止时间等]",
    "statement/constraints.md": "# 约束条件\n\n[记录假设、限制、工具规则等]",
    "analysis/problem_analysis.md": "# 问题分析\n\n[待填写]",
    "analysis/data_profile.md": "# 数据概况\n\n[待填写]",
    "model/assumptions.md": "# 建模假设\n\n[待填写]",
    "model/notation.md": "# 符号说明\n\n[待填写]",
    "model/candidates.md": "# 候选模型\n\n[待填写]",
    "model/selection.md": "# 模型选择\n\n[待填写]",
    "validation/plan.json": "{}",
    "paper/outline.md": "# 论文大纲\n\n[待填写]",
    "paper/final.md": "# 论文正文\n\n[待填写]",
    "paper/references.md": "# 参考文献\n\n[待填写]",
    "modeling/index.json": "{}",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data: dict) -> None:
    """原子写入 JSON 文件。"""
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def _default_index() -> dict:
    return {
        "schema_version": 2,
        "project": {
            "name": "",
            "type": "",
            "problem_type": [],
            "deadline": None,
        },
        "research_policy": {
            "rules_checked": False,
            "network_allowed": True,
            "external_sources_allowed": True,
            "constraint_source": None,
        },
        "current_phase": "intake",
        "status": "active",
        "subproblems": [],
        "assumptions": [],
        "notations": [],
        "model_candidates": [],
        "selected_models": [],
        "runs": [],
        "validations": [],
        "references": [],
        "paper_sections": [],
        "paper_deliverables": {
            "markdown": {
                "path": "paper/final.md",
                "status": "pending",
                "content_hash": None,
            },
            "docx": {
                "path": "paper/final.docx",
                "status": "pending",
                "build_record": "paper/build/docx-build.json",
                "content_hash": None,
            },
            "latex": {
                "project_path": "paper/latex",
                "main_tex": "paper/latex/main.tex",
                "status": "pending",
                "build_record": "paper/build/latex-build.json",
            },
            "pdf": {
                "path": "paper/final.pdf",
                "status": "pending",
                "source": "latex",
                "build_record": "paper/build/latex-build.json",
                "content_hash": None,
            },
        },
        "blockers": [],
        "next_actions": [],
        "completion_audit": {
            "passed": False,
            "checked_at": None,
            "evidence": [],
            "missing_items": [],
        },
        "phase_gates": {
            "intake": {
                "status": "pending",
                "checked_at": None,
                "evidence_paths": [],
                "input_hashes": {},
                "invalidated_at": None,
                "invalidated_reason": None,
            },
            "problem_analysis": {
                "status": "pending",
                "checked_at": None,
                "evidence_paths": [],
                "input_hashes": {},
                "invalidated_at": None,
                "invalidated_reason": None,
            },
            "literature_research": {
                "status": "pending",
                "checked_at": None,
                "evidence_paths": [],
                "input_hashes": {},
                "invalidated_at": None,
                "invalidated_reason": None,
            },
            "model_design": {
                "status": "pending",
                "checked_at": None,
                "evidence_paths": [],
                "input_hashes": {},
                "invalidated_at": None,
                "invalidated_reason": None,
            },
            "model_establishment": {
                "status": "pending",
                "checked_at": None,
                "evidence_paths": [],
                "input_hashes": {},
                "invalidated_at": None,
                "invalidated_reason": None,
            },
            "model_solving": {
                "status": "pending",
                "checked_at": None,
                "evidence_paths": [],
                "input_hashes": {},
                "invalidated_at": None,
                "invalidated_reason": None,
            },
            "model_validation": {
                "status": "pending",
                "checked_at": None,
                "evidence_paths": [],
                "input_hashes": {},
                "invalidated_at": None,
                "invalidated_reason": None,
            },
            "result_interpretation": {
                "status": "pending",
                "checked_at": None,
                "evidence_paths": [],
                "input_hashes": {},
                "invalidated_at": None,
                "invalidated_reason": None,
            },
            "paper_writing": {
                "status": "pending",
                "checked_at": None,
                "evidence_paths": [],
                "input_hashes": {},
                "invalidated_at": None,
                "invalidated_reason": None,
            },
            "paper_build": {
                "status": "pending",
                "checked_at": None,
                "evidence_paths": [],
                "input_hashes": {},
                "invalidated_at": None,
                "invalidated_reason": None,
            },
            "final_audit": {
                "status": "pending",
                "checked_at": None,
                "evidence_paths": [],
                "input_hashes": {},
                "invalidated_at": None,
                "invalidated_reason": None,
            },
        },
        "last_updated": None,
    }


def _is_placeholder_content(content: str) -> bool:
    """检查内容是否包含占位标记。"""
    return any(marker in content for marker in _PLACEHOLDER_MARKERS)


os_environ = __import__("os").environ


def _resolve_project_root(explicit: str | None) -> Path:
    """解析项目根目录，优先使用显式参数，其次使用环境变量。"""
    if explicit:
        root = Path(explicit).resolve()
    else:
        env_root = os_environ.get("AIASYS_WORKSPACE_ROOT")
        if not env_root:
            raise ValueError("未指定 --project-root 且 AIASYS_WORKSPACE_ROOT 未设置")
        root = Path(env_root).resolve()
    return root


def _create_directories(root: Path) -> list[str]:
    """创建目录，跳过已存在的。"""
    created: list[str] = []
    for rel in _DIR_LAYOUT:
        target = (root / rel).resolve()
        # 路径穿越检查：确保在 root 内
        try:
            target.relative_to(root)
        except ValueError:
            raise ValueError(f"路径穿越拒绝: {rel}")
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            created.append(rel)
    return created


def _create_placeholder_files(root: Path) -> tuple[list[str], list[str]]:
    """创建占位文件，跳过已存在的非空文件。返回 (created, skipped)。"""
    created: list[str] = []
    skipped: list[str] = []
    for rel, content in _PLACEHOLDER_FILES.items():
        target = (root / rel).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            raise ValueError(f"路径穿越拒绝: {rel}")
        if target.exists():
            if target.stat().st_size > 0:
                skipped.append(rel)
                continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        created.append(rel)
    return created, skipped


def _load_index_safe(root: Path) -> tuple[dict | None, str | None]:
    """安全加载 index.json，返回 (data, error)。"""
    index_path = (root / "modeling" / "index.json").resolve()
    try:
        index_path.relative_to(root)
    except ValueError:
        return None, "路径穿越拒绝: modeling/index.json"

    if not index_path.exists():
        return None, None

    try:
        raw = index_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None, "状态文件内容不是对象"
        return data, None
    except json.JSONDecodeError as exc:
        return None, f"状态文件 JSON 解析失败: {exc}"


def _init_index(root: Path) -> tuple[bool, str]:
    """初始化 modeling/index.json。

    已存在且合法时保持原文件，不覆盖。
    已存在但无法解析时返回错误。
    支持版本迁移：schema 1 → 2，保留全部原字段并补充新字段。
    """
    index_path = (root / "modeling" / "index.json").resolve()
    try:
        index_path.relative_to(root)
    except ValueError:
        raise ValueError("路径穿越拒绝: modeling/index.json")

    # 尝试加载现有文件
    existing, load_err = _load_index_safe(root)
    if load_err:
        # 文件存在但无法解析，返回错误
        if index_path.exists():
            return False, f"现有状态文件损坏且无法解析: {load_err}"

    if existing:
        schema_ver = existing.get("schema_version")
        if schema_ver == 2:
            # 合法且版本匹配，跳过
            return False, "已存在且版本匹配，跳过"
        elif schema_ver == 1:
            # 迁移：schema 1 → 2，保留全部原字段，补充新字段
            existing["schema_version"] = 2
            # 添加新字段（使用默认值）
            if "selected_models" not in existing:
                existing["selected_models"] = []
            if "runs" not in existing:
                existing["runs"] = []
            if "validations" not in existing:
                existing["validations"] = []
            # 迁移 validations 字段格式（从旧格式到新格式）
            for v in existing.get("validations", []):
                if "model_id" in v and "primary_model_ids" not in v:
                    v["primary_model_ids"] = [v["model_id"]]
                    del v["model_id"]
            existing["last_updated"] = _utc_now()
            _write_json(index_path, existing)
            return True, "从 schema 1 升级到 schema 2"
        else:
            # 无法识别的更高版本，返回错误，不覆盖
            return False, f"无法识别的 schema 版本: {schema_ver}"

    # 创建新文件
    data = _default_index()
    data["last_updated"] = _utc_now()
    _write_json(index_path, data)
    return True, "新建"


def init_project(project_root: str | Path | None = None, *, json_output: bool = False) -> dict:
    """主入口函数。

    Args:
        project_root: 项目根目录，未提供时从 AIASYS_WORKSPACE_ROOT 读取
        json_output: 是否输出 JSON 格式
    """
    root = _resolve_project_root(project_root)

    result: dict = {
        "project_root": str(root),
        "created_dirs": [],
        "created_files": [],
        "skipped_files": [],
        "index_action": "",
        "error": None,
    }

    try:
        result["created_dirs"] = _create_directories(root)
        created, skipped = _create_placeholder_files(root)
        result["created_files"] = created
        result["skipped_files"] = skipped
        action, msg = _init_index(root)
        result["index_action"] = msg
    except Exception as exc:
        result["error"] = str(exc)
        if json_output:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    if json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description="初始化数学建模项目")
    parser.add_argument(
        "--project-root", default=None, help="工作区根目录（默认读取 AIASYS_WORKSPACE_ROOT）"
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式结果")
    args = parser.parse_args()

    result = init_project(args.project_root, json_output=args.json)

    if result["error"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
