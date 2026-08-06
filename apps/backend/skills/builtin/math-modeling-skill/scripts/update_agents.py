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

os_environ = __import__("os").environ

_MARKER_START = "<!-- math-modeling:auto:start -->"
_MARKER_END = "<!-- math-modeling:auto:end -->"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_project_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    env_root = os_environ.get("AIASYS_WORKSPACE_ROOT")
    if not env_root:
        raise ValueError("未指定 --project-root 且 AIASYS_WORKSPACE_ROOT 未设置")
    return Path(env_root).resolve()


def _load_index_safe(root: Path) -> tuple[dict | None, str | None]:
    """安全加载 index.json，返回 (data, error)。"""
    index_path = root / "modeling" / "index.json"
    if not index_path.exists():
        return None, f"状态文件不存在: {index_path}"
    try:
        raw = index_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None, "状态文件内容不是对象"
        return data, None
    except json.JSONDecodeError as exc:
        return None, f"状态文件 JSON 解析失败: {exc}"


def _generate_agent_block(index: dict, root: Path) -> str:
    """根据 index.json 生成自动维护区块内容。"""
    project = index.get("project", {})
    current_phase = index.get("current_phase", "intake")
    project_status = index.get("status", "active")

    # 阶段描述映射
    phase_descriptions = {
        "intake": "材料接收与规则核验",
        "problem_analysis": "问题理解与拆解",
        "literature_research": "文献与资料检索",
        "model_design": "假设、符号与模型选择",
        "model_establishment": "模型建立",
        "model_solving": "编程求解与数值实验",
        "model_validation": "模型检验与敏感性分析",
        "result_interpretation": "结果解释与可视化",
        "paper_writing": "Markdown 文章撰写",
        "paper_build": "多格式构建与发布",
        "final_audit": "一致性检查与完成审计",
    }

    phase_desc = phase_descriptions.get(current_phase, current_phase)

    # 检查论文交付物状态
    paper_deliverables = index.get("paper_deliverables", {})
    deliverable_status = []
    if paper_deliverables:
        for fmt in ["markdown", "docx", "latex", "pdf"]:
            fmt_info = paper_deliverables.get(fmt, {})
            fmt_status = fmt_info.get("status", "pending")
            deliverable_status.append(f"{fmt}={fmt_status}")

    blockers = index.get("blockers", [])
    open_blockers = [b for b in blockers if b.get("status") == "open"]

    # 获取验证状态
    validations = index.get("validations", [])
    validation_summary = "无"
    if validations:
        latest_validation = validations[-1]
        validation_passed = latest_validation.get("passed", False)
        validation_summary = "通过" if validation_passed else "失败"

    lines = [
        _MARKER_START,
        "",
        "> 数学建模项目状态（自动维护）",
        "",
        f"- **项目名称**：{project.get('name', '未命名')}",
        f"- **当前阶段**：{current_phase}（{phase_desc}）",
        f"- **项目状态**：{project_status}",
    ]

    if deliverable_status:
        lines.append(f"- **论文交付物**：{', '.join(deliverable_status)}")

    # 添加验证状态摘要
    lines.append(f"- **验证状态**：{validation_summary}")

    if open_blockers:
        lines.append("")
        lines.append("**开放阻塞项**：")
        for b in open_blockers:
            req = "（需用户）" if b.get("requires_user") else ""
            lines.append(f"- {b.get('id')}: {b.get('reason')} {req}")

    lines.extend(
        [
            "",
            "**恢复方式**：读取 `modeling/index.json`，从 `current_phase` 恢复。",
            f"**运行环境**：{root}",
            "",
            _MARKER_END,
        ]
    )
    return "\n".join(lines)


def _update_agents_md(root: Path, index: dict) -> tuple[bool, str]:
    """更新 AGENTS.md，返回 (changed, message)。"""
    agents_path = root / "AGENTS.md"

    new_block = _generate_agent_block(index, root)

    if not agents_path.exists():
        # 创建新文件
        agents_path.write_text("# AGENTS.md\n\n" + new_block + "\n", encoding="utf-8")
        return True, "AGENTS.md 已创建"

    existing = agents_path.read_text(encoding="utf-8")

    start_idx = existing.find(_MARKER_START)
    end_idx = existing.find(_MARKER_END)

    if start_idx == -1 or end_idx == -1:
        # 标记不存在，追加到文件末尾
        agents_path.write_text(existing.rstrip() + "\n\n" + new_block + "\n", encoding="utf-8")
        return True, "自动区块已追加"

    # 替换标记之间的内容
    after_end = end_idx + len(_MARKER_END)
    new_content = existing[:start_idx] + new_block + existing[after_end:]

    if new_content != existing:
        agents_path.write_text(new_content, encoding="utf-8")
        return True, "自动区块已更新"

    return False, "内容未变化"


def update_agents(project_root: str | Path, *, json_output: bool = False) -> dict:
    """主入口函数。

    Args:
        project_root: 项目根目录
        json_output: 是否输出 JSON
    """
    root = _resolve_project_root(project_root)
    result: dict = {
        "project_root": str(root),
        "agents_updated": False,
        "message": "",
        "error": None,
    }

    try:
        index, load_err = _load_index_safe(root)
        if load_err:
            result["error"] = load_err
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            return result

        changed, msg = _update_agents_md(root, index)
        result["agents_updated"] = changed
        result["message"] = msg
    except Exception as exc:
        result["error"] = str(exc)

    if json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description="更新 AGENTS.md 数学建模区块")
    parser.add_argument("--project-root", default=None, help="工作区根目录")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式结果")
    args = parser.parse_args()
    result = update_agents(args.project_root, json_output=args.json)
    if result["error"]:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
