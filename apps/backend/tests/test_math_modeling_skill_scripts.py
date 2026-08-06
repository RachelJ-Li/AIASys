"""数学建模 Skill 脚本测试。"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1] / "skills" / "builtin" / "math-modeling-skill"
SCRIPTS = SKILL_ROOT / "scripts"


def run_cmd(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    """Run command with AIASYS_WORKSPACE_ROOT set."""
    env = {**os.environ, "AIASYS_WORKSPACE_ROOT": str(tmp_path)}
    result = subprocess.run(
        [sys.executable, *args],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return result


def run_validate(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    """Run validate_project.py with --project-root."""
    cmd_args = ["--project-root", str(tmp_path)]
    cmd_args.extend(args)
    return run_cmd(tmp_path, str(SCRIPTS / "validate_project.py"), *cmd_args)


def file_sha256(path: Path) -> str | None:
    """Calculate SHA256 hash of file."""
    if not path.exists():
        return None
    h = hashlib.sha256()
    try:
        h.update(path.read_bytes())
        return f"sha256:{h.hexdigest()}"
    except Exception:
        return None


# ============================================================
# 基础功能测试
# ============================================================


def test_skill_frontmatter_parsable() -> None:
    """TOML frontmatter 可解析."""
    skill_md = SKILL_ROOT / "SKILL.md"
    assert skill_md.exists(), "SKILL.md 不存在"
    content = skill_md.read_text(encoding="utf-8")
    assert content.startswith("+++"), "SKILL.md 应以 +++ 开头"
    assert 'name = "数学建模"' in content
    assert "description" in content


def test_skill_references_exist() -> None:
    """SKILL.md 引用的 reference 文件均存在."""
    skill_md = SKILL_ROOT / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    references_dir = SKILL_ROOT / "references"
    expected_refs = [
        "problem-analysis.md",
        "literature-research.md",
        "model-design.md",
        "model-solving.md",
        "model-validation.md",
        "paper-writing.md",
        "completion-audit.md",
        "schema.md",
        "workflow.md",
    ]
    for ref in expected_refs:
        assert (references_dir / ref).exists(), f"reference 文件缺失: {ref}"
        assert ref in content, f"SKILL.md 未引用 {ref}"


def test_all_phases_have_handlers() -> None:
    """所有 11 个阶段均存在处理器."""
    sys.path.insert(0, str(SCRIPTS))
    from validate_project import _PHASE_HANDLERS, _PHASE_ORDER

    assert len(_PHASE_ORDER) == 11, f"应有 11 个阶段，实际 {len(_PHASE_ORDER)}"
    for phase in _PHASE_ORDER:
        assert phase in _PHASE_HANDLERS, f"缺少 phase handler: {phase}"


def test_unknown_phase_exits_2(tmp_path: Path) -> None:
    """未知 phase 返回退出码 2."""
    result = run_validate(tmp_path, "--phase", "nonexistent", "--json")
    assert result.returncode == 2 or "未知阶段" in result.stdout


# ============================================================
# 阶段验证测试
# ============================================================


def test_all_checks_all_phases(tmp_path: Path) -> None:
    """--all 执行所有 11 个阶段."""
    # 手动创建必要的目录结构
    dirs = [
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
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)

    # 创建基本的 index.json
    index = {
        "schema_version": 2,
        "project": {"name": "test", "type": "math-modeling", "problem_type": ["optimization"]},
        "research_policy": {"rules_checked": True},
        "current_phase": "intake",
        "status": "active",
        "subproblems": [{"id": "P1", "status": "pending"}],
        "selected_models": [],
        "runs": [],
        "validations": [],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    (tmp_path / "modeling" / "index.json").write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--all", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    # 即使失败也应该有输出
    try:
        output = json.loads(result.stdout)
        assert "phase_results" in output
        assert len(output["phase_results"]) == 11, (
            f"应有 11 个阶段结果，实际 {len(output['phase_results'])}"
        )
    except json.JSONDecodeError:
        # 如果无法解析，说明有更严重的问题
        assert False, f"输出不是有效 JSON: {result.stdout}\n{result.stderr}"


def test_all_fails_on_first_failure(tmp_path: Path) -> None:
    """任一前序阶段失败时 --all 失败."""
    result = run_validate(tmp_path, "--all", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False


def test_json_output_parseable(tmp_path: Path) -> None:
    """所有 --json 输出都能被 json.loads() 解析."""
    result = run_validate(tmp_path, "--phase", "intake", "--json")
    json.loads(result.stdout)


# ============================================================
# 交付物验证测试
# ============================================================


def test_final_audit_fails_with_only_markdown(tmp_path: Path) -> None:
    """只有 Markdown 时 final_audit 必须失败."""
    (tmp_path / "statement").mkdir(parents=True, exist_ok=True)
    (tmp_path / "statement" / "problem.md").write_text("# 赛题\n测试", encoding="utf-8")
    (tmp_path / "statement" / "requirements.md").write_text("# 要求\n测试", encoding="utf-8")
    (tmp_path / "statement" / "constraints.md").write_text("# 约束\n测试", encoding="utf-8")
    (tmp_path / "analysis").mkdir(parents=True, exist_ok=True)
    (tmp_path / "analysis" / "problem_analysis.md").write_text("# 分析\n测试", encoding="utf-8")
    (tmp_path / "analysis" / "data_profile.md").write_text("# 数据\n测试", encoding="utf-8")
    (tmp_path / "paper").mkdir(parents=True, exist_ok=True)
    (tmp_path / "paper" / "final.md").write_text("# 论文\n测试", encoding="utf-8")
    (tmp_path / "paper" / "references.md").write_text("# 参考文献\n测试", encoding="utf-8")
    (tmp_path / "paper" / "outline.md").write_text("# 大纲\n测试", encoding="utf-8")

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 1,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "research_policy": {"rules_checked": True},
        "current_phase": "final_audit",
        "status": "active",
        "subproblems": [{"id": "P1", "status": "completed"}],
        "selected_models": [{"model_id": "M1", "subproblem_ids": ["P1"]}],
        "runs": [
            {
                "run_id": "run-001",
                "model_id": "M1",
                "command": "test",
                "status": "succeeded",
                "log_paths": ["runs/run-001.log"],
                "result_paths": ["runs/run-001.json"],
            }
        ],
        "validations": [
            {
                "validation_id": "V1",
                "model_id": "M1",
                "run_ids": ["run-001"],
                "passed": True,
                "evidence_paths": ["validation/evidence.txt"],
            }
        ],
        "paper_deliverables": {"markdown": {"status": "completed", "path": "paper/final.md"}},
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "final_audit", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("missing", []) + output.get("invalid", [])
    assert any("docx" in issue or "latex" in issue or "pdf" in issue for issue in all_issues), (
        f"应检查到缺少 Word/LaTeX/PDF: {all_issues}"
    )


def test_invalid_docx_format_fails(tmp_path: Path) -> None:
    """DOCX 不是合法 OOXML ZIP 时必须失败."""
    (tmp_path / "statement").mkdir(parents=True, exist_ok=True)
    (tmp_path / "statement" / "problem.md").write_text("# 赛题\n测试", encoding="utf-8")
    (tmp_path / "statement" / "requirements.md").write_text("# 要求\n测试", encoding="utf-8")
    (tmp_path / "statement" / "constraints.md").write_text("# 约束\n测试", encoding="utf-8")
    (tmp_path / "analysis").mkdir(parents=True, exist_ok=True)
    (tmp_path / "analysis" / "problem_analysis.md").write_text("# 分析\n测试", encoding="utf-8")
    (tmp_path / "analysis" / "data_profile.md").write_text("# 数据\n测试", encoding="utf-8")
    (tmp_path / "paper").mkdir(parents=True, exist_ok=True)
    (tmp_path / "paper" / "final.docx").write_text("not a docx", encoding="utf-8")

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 1,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "research_policy": {"rules_checked": True},
        "current_phase": "final_audit",
        "status": "active",
        "subproblems": [{"id": "P1", "status": "completed"}],
        "selected_models": [{"model_id": "M1", "subproblem_ids": ["P1"]}],
        "runs": [
            {
                "run_id": "run-001",
                "model_id": "M1",
                "command": "test",
                "status": "succeeded",
                "log_paths": ["runs/run-001.log"],
                "result_paths": ["runs/run-001.json"],
            }
        ],
        "validations": [
            {
                "validation_id": "V1",
                "model_id": "M1",
                "run_ids": ["run-001"],
                "passed": True,
                "evidence_paths": ["validation/evidence.txt"],
            }
        ],
        "paper_deliverables": {"docx": {"status": "completed", "path": "paper/final.docx"}},
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs" / "run-001.log").write_text("log", encoding="utf-8")
    (tmp_path / "runs" / "run-001.json").write_text("{}", encoding="utf-8")
    (tmp_path / "validation").mkdir(parents=True, exist_ok=True)
    (tmp_path / "validation" / "evidence.txt").write_text("evidence", encoding="utf-8")
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "final_audit", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("invalid", [])
    assert any("DOCX" in issue and "无效" in issue for issue in all_issues), (
        f"应检查到 DOCX 格式无效: {all_issues}"
    )


def test_pdf_missing_build_record_is_rejected(tmp_path: Path) -> None:
    """PDF 缺少 build_record 时应失败。"""
    (tmp_path / "paper").mkdir(parents=True, exist_ok=True)
    pdf_file = tmp_path / "paper" / "final.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake pdf" + b" " * 200)

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "research_policy": {"rules_checked": True},
        "current_phase": "paper_build",
        "status": "active",
        "subproblems": [{"id": "P1", "status": "completed"}],
        "selected_models": [{"model_id": "M1", "subproblem_ids": ["P1"]}],
        "runs": [
            {
                "run_id": "run-001",
                "model_id": "M1",
                "command": "test",
                "status": "succeeded",
                "log_paths": ["runs/run-001.log"],
                "result_paths": ["runs/run-001.json"],
            }
        ],
        "paper_deliverables": {
            "markdown": {"path": "paper/final.md", "status": "completed"},
            "docx": {
                "path": "paper/final.docx",
                "status": "completed",
                "build_record": "paper/build/docx-build.json",
            },
            "latex": {
                "project_path": "paper/latex",
                "main_tex": "paper/latex/main.tex",
                "status": "completed",
                "build_record": "paper/build/latex-build.json",
            },
            "pdf": {"path": "paper/final.pdf", "status": "completed"},  # 缺少 build_record
        },
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs" / "run-001.log").write_text("log", encoding="utf-8")
    (tmp_path / "runs" / "run-001.json").write_text("{}", encoding="utf-8")
    (tmp_path / "paper" / "build").mkdir(parents=True, exist_ok=True)
    (tmp_path / "paper" / "build" / "docx-build.json").write_text("{}", encoding="utf-8")
    (tmp_path / "paper" / "build" / "latex-build.json").write_text("{}", encoding="utf-8")
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "paper_build", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    assert any("build_record" in issue for issue in output.get("invalid", [])), (
        f"应检查到缺少 build_record: {output}"
    )


def test_pdf_requires_parser_library(tmp_path: Path) -> None:
    """PDF 解析库不可用时审核失败."""
    import sys
    from unittest.mock import MagicMock

    # 阻止 pypdf 和 fitz 导入
    sys.modules["pypdf"] = MagicMock()
    sys.modules["pypdf"].PdfReader.side_effect = ImportError("No module named 'pypdf'")
    sys.modules["fitz"] = MagicMock()
    sys.modules["fitz"].open.side_effect = ImportError("No module named 'fitz'")

    # 直接加载 validate_project 模块
    sys.path.insert(0, str(SCRIPTS))
    from validate_project import _check_pdf_source

    (tmp_path / "paper").mkdir(parents=True, exist_ok=True)
    pdf_file = tmp_path / "paper" / "final.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake pdf with enough content to pass size check" + b" " * 200)

    (tmp_path / "paper" / "build").mkdir(parents=True, exist_ok=True)
    pdf_hash = file_sha256(pdf_file)
    latex_build = {
        "status": "succeeded",
        "engine": "xelatex",
        "command": "xelatex main.tex",
        "return_code": 0,
        "main_tex": "paper/latex/main.tex",
        "source_hashes": {"paper/latex/main.tex": "sha256:test"},
        "pdf_path": "paper/final.pdf",
        "pdf_sha256": pdf_hash,
        "log_path": "paper/build/latex-compile.log",
        "started_at": "2025-01-01T00:00:00",
        "finished_at": "2025-01-01T00:00:01",
    }
    (tmp_path / "paper" / "build" / "latex-build.json").write_text(
        json.dumps(latex_build), encoding="utf-8"
    )

    # 直接调用 _check_pdf_source
    valid, err = _check_pdf_source(tmp_path, "paper/final.pdf", "paper/build/latex-build.json")
    assert valid is False, f"PDF 解析库不可用时应失败: {err}"
    assert "PDF 解析库不可用" in err, f"错误信息应包含'PDF 解析库不可用': {err}"


# ============================================================
# 路径安全测试
# ============================================================


def test_outside_project_path_rejected(tmp_path: Path) -> None:
    """项目外路径被拒绝."""
    index_path = tmp_path / "modeling" / "index.json"
    outside_path = str(tmp_path.parent / "outside.txt")
    Path(outside_path).write_text("evil", encoding="utf-8")

    index = {
        "schema_version": 1,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "research_policy": {"rules_checked": True},
        "current_phase": "model_solving",
        "status": "active",
        "runs": [
            {
                "run_id": "run-001",
                "model_id": "M1",
                "command": "test",
                "status": "succeeded",
                "log_paths": [outside_path],
                "result_paths": [],
            }
        ],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_solving", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("invalid", [])
    assert any("路径" in issue or "逃逸" in issue or "无效" in issue for issue in all_issues), (
        f"应检测到路径问题: {all_issues}"
    )


# ============================================================
# 只读验证测试
# ============================================================


def test_readonly_validation_no_changes(tmp_path: Path) -> None:
    """不带 --record 时文件不变."""
    (tmp_path / "statement").mkdir(parents=True, exist_ok=True)
    (tmp_path / "statement" / "problem.md").write_text("# 赛题\n测试", encoding="utf-8")
    (tmp_path / "statement" / "requirements.md").write_text("# 要求\n测试", encoding="utf-8")
    (tmp_path / "statement" / "constraints.md").write_text("# 约束\n测试", encoding="utf-8")

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 1,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "research_policy": {"rules_checked": True},
        "current_phase": "intake",
        "status": "active",
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    initial_content = json.dumps(index, ensure_ascii=False)
    index_path.write_text(initial_content, encoding="utf-8")
    initial_mtime = index_path.stat().st_mtime

    result = run_validate(tmp_path, "--phase", "intake", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is True

    final_content = index_path.read_text(encoding="utf-8")
    final_mtime = index_path.stat().st_mtime

    assert initial_content == final_content, "不带 --record 时 index.json 不应被修改"
    assert initial_mtime == final_mtime, "不带 --record 时 index.json 的修改时间不应改变"


# ============================================================
# 验证计划测试
# ============================================================


def test_validation_plan_rejects_empty_criteria(tmp_path: Path) -> None:
    """验证计划 criteria 为空时必须失败."""
    (tmp_path / "validation").mkdir(parents=True, exist_ok=True)
    plan_path = tmp_path / "validation" / "plan.json"
    plan_path.write_text(json.dumps({"criteria": []}), encoding="utf-8")

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_establishment",
        "status": "active",
        "selected_models": [{"model_id": "M1", "subproblem_ids": ["P1"]}],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_establishment", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("invalid", [])
    assert any("criteria 为空" in issue for issue in all_issues), (
        f"应检查到 criteria 为空: {all_issues}"
    )


def test_validation_plan_rejects_missing_threshold_source(tmp_path: Path) -> None:
    """验证计划条件缺少 threshold 或 source 时必须失败."""
    (tmp_path / "validation").mkdir(parents=True, exist_ok=True)
    plan_path = tmp_path / "validation" / "plan.json"
    plan = {
        "primary_model_ids": ["M1"],
        "baseline_model_ids": ["B1"],
        "criteria": [
            {"criterion_id": "C1", "metric": "rmse", "direction": "minimize", "operator": "<="}
            # 缺少 threshold 和 source
        ],
    }
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_establishment",
        "status": "active",
        "selected_models": [
            {
                "model_id": "M1",
                "subproblem_ids": ["P1"],
                "role": "primary",
                "baseline_model_ids": ["B1"],
            },
            {
                "model_id": "B1",
                "subproblem_ids": ["P1"],
                "role": "baseline",
                "baseline_for": ["M1"],
            },
        ],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_establishment", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("invalid", [])
    assert any("threshold" in issue for issue in all_issues), (
        f"应检查到缺少 threshold: {all_issues}"
    )
    assert any("source" in issue for issue in all_issues), f"应检查到缺少 source: {all_issues}"


# ============================================================
# 基线测试
# ============================================================


def test_validation_rejects_missing_baseline_without_exemption(tmp_path: Path) -> None:
    """主模型无基线且无豁免时应失败."""
    (tmp_path / "validation").mkdir(parents=True, exist_ok=True)
    plan_path = tmp_path / "validation" / "plan.json"
    plan = {
        "primary_model_ids": ["M1"],
        "baseline_model_ids": [],  # 空基线列表
        "criteria": [
            {
                "criterion_id": "C1",
                "metric": "rmse",
                "direction": "minimize",
                "operator": "<=",
                "threshold": 10.0,
                "source": "赛题要求",
            }
        ],
    }
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_design",
        "status": "active",
        "selected_models": [
            {"model_id": "M1", "subproblem_ids": ["P1"], "role": "primary"}
        ],  # 无基线
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_design", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("invalid", [])
    assert any("基线" in issue for issue in all_issues), f"应检查到缺少基线: {all_issues}"


# ============================================================
# 基线豁免测试（新增）
# ============================================================


def test_valid_baseline_exemption_passes(tmp_path: Path) -> None:
    """基线豁免信息完整时应通过基线检查."""
    (tmp_path / "validation").mkdir(parents=True, exist_ok=True)
    (tmp_path / "model").mkdir(parents=True, exist_ok=True)

    plan_path = tmp_path / "validation" / "plan.json"
    plan = {
        "primary_model_ids": ["M1"],
        "baseline_model_ids": [],
        "criteria": [
            {
                "criterion_id": "C1",
                "metric": "rmse",
                "direction": "minimize",
                "operator": "<=",
                "threshold": 10.0,
                "source": "赛题要求",
            }
        ],
    }
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    # 创建模型设计必需文件
    (tmp_path / "model" / "assumptions.md").write_text("# 建模假设\n测试", encoding="utf-8")
    (tmp_path / "model" / "notation.md").write_text("# 符号说明\n测试", encoding="utf-8")

    # 创建豁免证据文件
    evidence_path = tmp_path / "model" / "selection.md"
    evidence_path.write_text("# 模型选择\n基线豁免证据", encoding="utf-8")

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_design",
        "status": "active",
        "selected_models": [
            {
                "model_id": "M1",
                "subproblem_ids": ["P1"],
                "role": "primary",
                "baseline_exemption": {
                    "reason": "不存在可运行的同类基线",
                    "evidence_paths": ["model/selection.md"],
                    "alternative": "解析解对比与消融实验",
                },
            }
        ],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_design", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is True, f"有效豁免应通过: {output.get('invalid', [])}"


def test_invalid_baseline_exemption_missing_reason_fails(tmp_path: Path) -> None:
    """基线豁免缺少 reason 时应失败."""
    (tmp_path / "model").mkdir(parents=True, exist_ok=True)
    (tmp_path / "model" / "assumptions.md").write_text("# 建模假设\n测试", encoding="utf-8")
    (tmp_path / "model" / "notation.md").write_text("# 符号说明\n测试", encoding="utf-8")

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_design",
        "status": "active",
        "selected_models": [
            {
                "model_id": "M1",
                "subproblem_ids": ["P1"],
                "role": "primary",
                "baseline_exemption": {
                    # 缺少 reason
                    "evidence_paths": ["model/selection.md"],
                    "alternative": "解析解对比",
                },
            }
        ],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    (tmp_path / "model" / "selection.md").write_text("# 模型选择", encoding="utf-8")
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_design", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("invalid", [])
    assert any("reason" in issue for issue in all_issues), f"应检查到缺少 reason: {all_issues}"


# ============================================================
# 运行检查测试（新增）
# ============================================================


def test_missing_primary_run_fails(tmp_path: Path) -> None:
    """主模型缺少成功全量运行时应失败."""
    (tmp_path / "validation").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs").mkdir(parents=True, exist_ok=True)
    plan_path = tmp_path / "validation" / "plan.json"
    plan = {
        "primary_model_ids": ["M1"],
        "baseline_model_ids": ["B1"],
        "protocol_hash": "sha256:abc123",
        "dataset_split_id": "split-001",
        "criteria": [
            {
                "criterion_id": "C1",
                "metric": "rmse",
                "direction": "minimize",
                "operator": "<=",
                "threshold": 10.0,
                "source": "赛题要求",
            }
        ],
    }
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_solving",
        "status": "active",
        "selected_models": [
            {
                "model_id": "M1",
                "subproblem_ids": ["P1"],
                "role": "primary",
                "baseline_model_ids": ["B1"],
            },
            {"model_id": "B1", "subproblem_ids": ["P1"], "role": "baseline"},
        ],
        "runs": [
            {
                "run_id": "run-B1",
                "model_id": "B1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
            }
        ],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_solving", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("invalid", []) + output.get("missing", [])
    assert any("M1" in issue and ("运行" in issue or "全量" in issue) for issue in all_issues), (
        f"应检查到主模型缺少运行: {all_issues}"
    )


def test_missing_baseline_run_fails(tmp_path: Path) -> None:
    """基线模型缺少成功全量运行时应失败."""
    (tmp_path / "validation").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs").mkdir(parents=True, exist_ok=True)
    plan_path = tmp_path / "validation" / "plan.json"
    plan = {
        "primary_model_ids": ["M1"],
        "baseline_model_ids": ["B1"],
        "protocol_hash": "sha256:abc123",
        "dataset_split_id": "split-001",
        "criteria": [
            {
                "criterion_id": "C1",
                "metric": "rmse",
                "direction": "minimize",
                "operator": "<=",
                "threshold": 10.0,
                "source": "赛题要求",
            }
        ],
    }
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_solving",
        "status": "active",
        "selected_models": [
            {
                "model_id": "M1",
                "subproblem_ids": ["P1"],
                "role": "primary",
                "baseline_model_ids": ["B1"],
            },
            {"model_id": "B1", "subproblem_ids": ["P1"], "role": "baseline"},
        ],
        "runs": [
            {
                "run_id": "run-001",
                "model_id": "M1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
                "command": "python run_M1.py",
                "log_paths": ["runs/run-001.log"],
                "result_paths": ["runs/run-001.json"],
            }
        ],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_solving", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("invalid", []) + output.get("missing", [])
    assert any("B1" in issue and ("运行" in issue or "全量" in issue) for issue in all_issues), (
        f"应检查到基线模型缺少运行: {all_issues}"
    )


def test_protocol_hash_mismatch_fails(tmp_path: Path) -> None:
    """协议哈希不一致时应失败."""
    (tmp_path / "validation").mkdir(parents=True, exist_ok=True)
    plan_path = tmp_path / "validation" / "plan.json"
    plan = {
        "primary_model_ids": ["M1"],
        "baseline_model_ids": ["B1"],
        "protocol_hash": "sha256:abc123",
        "dataset_split_id": "split-001",
        "criteria": [
            {
                "criterion_id": "C1",
                "metric": "rmse",
                "direction": "minimize",
                "operator": "<=",
                "threshold": 10.0,
                "source": "赛题要求",
            }
        ],
    }
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_solving",
        "status": "active",
        "selected_models": [
            {
                "model_id": "M1",
                "subproblem_ids": ["P1"],
                "role": "primary",
                "baseline_model_ids": ["B1"],
            },
            {"model_id": "B1", "subproblem_ids": ["P1"], "role": "baseline"},
        ],
        "runs": [
            {
                "run_id": "run-M1",
                "model_id": "M1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
            },
            {
                "run_id": "run-B1",
                "model_id": "B1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:xyz789",
                "dataset_split_id": "split-001",
            },  # 哈希不一致
        ],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_solving", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("invalid", [])
    assert any("protocol_hash" in issue for issue in all_issues), (
        f"应检查到协议哈希不一致: {all_issues}"
    )


def test_dataset_split_mismatch_fails(tmp_path: Path) -> None:
    """数据集划分不一致时应失败."""
    (tmp_path / "validation").mkdir(parents=True, exist_ok=True)
    plan_path = tmp_path / "validation" / "plan.json"
    plan = {
        "primary_model_ids": ["M1"],
        "baseline_model_ids": ["B1"],
        "protocol_hash": "sha256:abc123",
        "dataset_split_id": "split-001",
        "criteria": [
            {
                "criterion_id": "C1",
                "metric": "rmse",
                "direction": "minimize",
                "operator": "<=",
                "threshold": 10.0,
                "source": "赛题要求",
            }
        ],
    }
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_solving",
        "status": "active",
        "selected_models": [
            {
                "model_id": "M1",
                "subproblem_ids": ["P1"],
                "role": "primary",
                "baseline_model_ids": ["B1"],
            },
            {"model_id": "B1", "subproblem_ids": ["P1"], "role": "baseline"},
        ],
        "runs": [
            {
                "run_id": "run-M1",
                "model_id": "M1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
            },
            {
                "run_id": "run-B1",
                "model_id": "B1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-002",
            },  # 划分不一致
        ],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_solving", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("invalid", [])
    assert any("dataset_split_id" in issue for issue in all_issues), (
        f"应检查到数据集划分不一致: {all_issues}"
    )


# ============================================================
# 验证结果测试（新增）
# ============================================================


def test_missing_comparison_fails(tmp_path: Path) -> None:
    """验证结果缺少 comparisons 时应失败."""
    (tmp_path / "validation").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs" / "run-001.log").write_text("log", encoding="utf-8")
    (tmp_path / "runs" / "run-001.json").write_text("{}", encoding="utf-8")

    plan_path = tmp_path / "validation" / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "primary_model_ids": ["M1"],
                "baseline_model_ids": ["B1"],
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
                "criteria": [
                    {
                        "criterion_id": "C1",
                        "metric": "rmse",
                        "direction": "minimize",
                        "operator": "<=",
                        "threshold": 10.0,
                        "source": "赛题要求",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    validation_path = tmp_path / "validation" / "validation.json"
    validation_path.write_text(
        json.dumps(
            {
                "evaluations": [
                    {"model_id": "M1", "metrics": {"rmse": 8.2}},
                    {"model_id": "B1", "metrics": {"rmse": 11.6}},
                ],
                "criteria_results": [
                    {"criterion_id": "C1", "observed": 8.2, "passed": True, "required": True}
                ],
                # 缺少 comparisons
                "stability_results": [{"criterion_id": "S1", "passed": True}],
                "domain_results": [],
                "passed": True,
                "evidence_paths": ["validation/validation.md"],
            }
        ),
        encoding="utf-8",
    )

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_validation",
        "status": "active",
        "selected_models": [
            {
                "model_id": "M1",
                "subproblem_ids": ["P1"],
                "role": "primary",
                "baseline_model_ids": ["B1"],
            },
            {"model_id": "B1", "subproblem_ids": ["P1"], "role": "baseline"},
        ],
        "runs": [
            {
                "run_id": "run-M1",
                "model_id": "M1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
            },
            {
                "run_id": "run-B1",
                "model_id": "B1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
            },
        ],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_validation", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("invalid", [])
    assert any("comparisons" in issue for issue in all_issues), (
        f"应检查到缺少 comparisons: {all_issues}"
    )


def test_missing_stability_fails(tmp_path: Path) -> None:
    """验证结果缺少稳定性检查时应失败."""
    (tmp_path / "validation").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs" / "run-001.log").write_text("log", encoding="utf-8")
    (tmp_path / "runs" / "run-001.json").write_text("{}", encoding="utf-8")

    plan_path = tmp_path / "validation" / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "primary_model_ids": ["M1"],
                "baseline_model_ids": ["B1"],
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
                "criteria": [
                    {
                        "criterion_id": "C1",
                        "metric": "rmse",
                        "direction": "minimize",
                        "operator": "<=",
                        "threshold": 10.0,
                        "source": "赛题要求",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    validation_path = tmp_path / "validation" / "validation.json"
    validation_path.write_text(
        json.dumps(
            {
                "evaluations": [
                    {"model_id": "M1", "metrics": {"rmse": 8.2}},
                    {"model_id": "B1", "metrics": {"rmse": 11.6}},
                ],
                "criteria_results": [
                    {"criterion_id": "C1", "observed": 8.2, "passed": True, "required": True}
                ],
                "comparisons": [
                    {
                        "metric": "rmse",
                        "primary_model_id": "M1",
                        "baseline_model_id": "B1",
                        "primary_value": 8.2,
                        "baseline_value": 11.6,
                        "absolute_delta": -3.4,
                        "relative_improvement": 0.29,
                        "same_protocol": True,
                    }
                ],
                "stability_results": [],  # 空稳定性结果
                "domain_results": [],
                "passed": True,
                "evidence_paths": ["validation/validation.md"],
            }
        ),
        encoding="utf-8",
    )

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_validation",
        "status": "active",
        "selected_models": [
            {
                "model_id": "M1",
                "subproblem_ids": ["P1"],
                "role": "primary",
                "baseline_model_ids": ["B1"],
            },
            {"model_id": "B1", "subproblem_ids": ["P1"], "role": "baseline"},
        ],
        "runs": [
            {
                "run_id": "run-M1",
                "model_id": "M1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
            },
            {
                "run_id": "run-B1",
                "model_id": "B1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
            },
        ],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_validation", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("invalid", [])
    assert any("稳定性" in issue for issue in all_issues), f"应检查到缺少稳定性: {all_issues}"


def test_domain_validation_required_for_biological(tmp_path: Path) -> None:
    """生物模型缺少领域验证时应失败."""
    (tmp_path / "validation").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs" / "run-001.log").write_text("log", encoding="utf-8")
    (tmp_path / "runs" / "run-001.json").write_text("{}", encoding="utf-8")
    (tmp_path / "validation" / "validation.md").write_text("# 验证报告", encoding="utf-8")

    plan_path = tmp_path / "validation" / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "primary_model_ids": ["M1"],
                "baseline_model_ids": ["B1"],
                "problem_type": ["biological"],
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
                "criteria": [
                    {
                        "criterion_id": "C1",
                        "metric": "p_value",
                        "direction": "minimize",
                        "operator": "<=",
                        "threshold": 0.05,
                        "source": "文献",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    validation_path = tmp_path / "validation" / "validation.json"
    validation_path.write_text(
        json.dumps(
            {
                "evaluations": [
                    {"model_id": "M1", "metrics": {"p_value": 0.01}},
                    {"model_id": "B1", "metrics": {"p_value": 0.03}},
                ],
                "criteria_results": [
                    {"criterion_id": "C1", "observed": 0.01, "passed": True, "required": True}
                ],
                "comparisons": [
                    {
                        "metric": "p_value",
                        "primary_value": 0.01,
                        "baseline_value": 0.03,
                        "absolute_delta": -0.02,
                        "relative_improvement": 0.67,
                        "same_protocol": True,
                    }
                ],
                "stability_results": [{"criterion_id": "S1", "passed": True}],
                "domain_results": [],  # 空领域结果，但生物模型需要领域验证
                "passed": True,
                "evidence_paths": ["validation/validation.md"],
            }
        ),
        encoding="utf-8",
    )

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["biological"]},
        "current_phase": "model_validation",
        "status": "active",
        "selected_models": [
            {
                "model_id": "M1",
                "subproblem_ids": ["P1"],
                "role": "primary",
                "baseline_model_ids": ["B1"],
            },
            {"model_id": "B1", "subproblem_ids": ["P1"], "role": "baseline"},
        ],
        "runs": [
            {
                "run_id": "run-M1",
                "model_id": "M1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
            },
            {
                "run_id": "run-B1",
                "model_id": "B1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
            },
        ],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_validation", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("invalid", [])
    assert any("领域验证" in issue or "domain_results" in issue for issue in all_issues), (
        f"应检查到缺少领域验证: {all_issues}"
    )


# ============================================================
# 多模型对比测试（新增）
# ============================================================


def test_multi_primary_models_supported(tmp_path: Path) -> None:
    """支持多个主模型和基线的协议检查."""
    (tmp_path / "validation").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs").mkdir(parents=True, exist_ok=True)

    # 添加最小运行记录
    (tmp_path / "runs" / "run-minimum.log").write_text("log-minimum", encoding="utf-8")
    (tmp_path / "runs" / "run-minimum.json").write_text("{}", encoding="utf-8")
    (tmp_path / "runs" / "run-M1.log").write_text("log-M1", encoding="utf-8")
    (tmp_path / "runs" / "run-M1.json").write_text("{}", encoding="utf-8")
    (tmp_path / "runs" / "run-M2.log").write_text("log-M2", encoding="utf-8")
    (tmp_path / "runs" / "run-M2.json").write_text("{}", encoding="utf-8")
    (tmp_path / "runs" / "run-B1.log").write_text("log-B1", encoding="utf-8")
    (tmp_path / "runs" / "run-B1.json").write_text("{}", encoding="utf-8")
    (tmp_path / "runs" / "run-B2.log").write_text("log-B2", encoding="utf-8")
    (tmp_path / "runs" / "run-B2.json").write_text("{}", encoding="utf-8")

    plan_path = tmp_path / "validation" / "plan.json"
    plan = {
        "primary_model_ids": ["M1", "M2"],  # 多个主模型
        "baseline_model_ids": ["B1", "B2"],  # 多个基线
        "protocol_hash": "sha256:abc123",
        "dataset_split_id": "split-001",
        "criteria": [
            {
                "criterion_id": "C1",
                "metric": "rmse",
                "direction": "minimize",
                "operator": "<=",
                "threshold": 10.0,
                "source": "赛题要求",
            }
        ],
    }
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_solving",
        "status": "active",
        "selected_models": [
            {
                "model_id": "M1",
                "subproblem_ids": ["P1"],
                "role": "primary",
                "baseline_model_ids": ["B1"],
            },
            {
                "model_id": "M2",
                "subproblem_ids": ["P1"],
                "role": "primary",
                "baseline_model_ids": ["B2"],
            },
            {"model_id": "B1", "subproblem_ids": ["P1"], "role": "baseline"},
            {"model_id": "B2", "subproblem_ids": ["P1"], "role": "baseline"},
        ],
        "runs": [
            {
                "run_id": "run-minimum",
                "model_id": "M1",
                "status": "succeeded",
                "run_scope": "minimum",
                "minimum_gate_passed": True,
                "command": "python run_minimum.py",
                "log_paths": ["runs/run-minimum.log"],
                "result_paths": ["runs/run-minimum.json"],
            },
            {
                "run_id": "run-M1",
                "model_id": "M1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
                "command": "python run_M1.py",
                "log_paths": ["runs/run-M1.log"],
                "result_paths": ["runs/run-M1.json"],
            },
            {
                "run_id": "run-M2",
                "model_id": "M2",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
                "command": "python run_M2.py",
                "log_paths": ["runs/run-M2.log"],
                "result_paths": ["runs/run-M2.json"],
            },
            {
                "run_id": "run-B1",
                "model_id": "B1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
                "command": "python run_B1.py",
                "log_paths": ["runs/run-B1.log"],
                "result_paths": ["runs/run-B1.json"],
            },
            {
                "run_id": "run-B2",
                "model_id": "B2",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
                "command": "python run_B2.py",
                "log_paths": ["runs/run-B2.log"],
                "result_paths": ["runs/run-B2.json"],
            },
        ],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_solving", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    # 所有主模型和基线都有运行且协议一致，应通过
    assert output["passed"] is True, f"多模型协议一致应通过: {output.get('invalid', [])}"


# ============================================================
# 门禁失效测试（新增）
# ============================================================


def test_gate_invalidation_on_input_change(tmp_path: Path) -> None:
    """输入文件变化应导致门禁失效."""
    (tmp_path / "statement").mkdir(parents=True, exist_ok=True)
    (tmp_path / "statement" / "problem.md").write_text("# 赛题\nv1", encoding="utf-8")

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_solving",
        "status": "active",
        "runs": [
            {
                "run_id": "run-001",
                "model_id": "M1",
                "status": "succeeded",
                "input_hashes": {"statement/problem.md": "sha256:old_hash"},
            }
        ],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    # 修改输入文件
    (tmp_path / "statement" / "problem.md").write_text("# 赛题\nv2", encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_solving", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("invalid", []) + output.get("warnings", [])
    assert any("已修改" in issue or "变化" in issue for issue in all_issues), (
        f"应检测到输入文件变化: {all_issues}"
    )


def test_outside_path_in_gate_invalidation_rejected(tmp_path: Path) -> None:
    """门禁失效检查中项目外路径应被拒绝."""
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    outside_path = str(tmp_path.parent / "outside.txt")
    Path(outside_path).write_text("evil", encoding="utf-8")

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_solving",
        "status": "active",
        "runs": [
            {
                "run_id": "run-001",
                "model_id": "M1",
                "status": "succeeded",
                "input_hashes": {
                    "../outside.txt": "sha256:fake_hash"  # 项目外路径
                },
            }
        ],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_solving", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is False
    all_issues = output.get("invalid", []) + output.get("warnings", [])
    assert any("路径" in issue or "逃逸" in issue or "无效" in issue for issue in all_issues), (
        f"应检测到路径问题: {all_issues}"
    )


# ============================================================
# 可选条件测试（新增）
# ============================================================


def test_optional_criteria_failure_allows_pass(tmp_path: Path) -> None:
    """可选条件失败不应导致整体失败."""
    (tmp_path / "validation").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs" / "run-001.log").write_text("log", encoding="utf-8")
    (tmp_path / "runs" / "run-001.json").write_text("{}", encoding="utf-8")
    (tmp_path / "validation" / "validation.md").write_text("# 验证报告", encoding="utf-8")

    plan_path = tmp_path / "validation" / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "primary_model_ids": ["M1"],
                "baseline_model_ids": ["B1"],
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
                "criteria": [
                    {
                        "criterion_id": "C1",
                        "metric": "rmse",
                        "direction": "minimize",
                        "operator": "<=",
                        "threshold": 10.0,
                        "source": "赛题要求",
                        "required": True,
                    },
                    {
                        "criterion_id": "C2",
                        "metric": "r2",
                        "direction": "maximize",
                        "operator": ">=",
                        "threshold": 0.8,
                        "source": "文献",
                        "required": False,
                    },  # 可选
                ],
            }
        ),
        encoding="utf-8",
    )

    validation_path = tmp_path / "validation" / "validation.json"
    validation_path.write_text(
        json.dumps(
            {
                "evaluations": [
                    {"model_id": "M1", "metrics": {"rmse": 8.2, "r2": 0.75}},  # r2 不满足条件
                    {"model_id": "B1", "metrics": {"rmse": 11.6, "r2": 0.82}},
                ],
                "comparisons": [
                    {
                        "metric": "rmse",
                        "primary_model_id": "M1",
                        "baseline_model_id": "B1",
                        "primary_value": 8.2,
                        "baseline_value": 11.6,
                        "absolute_delta": -3.4,
                        "relative_improvement": 0.29,
                        "same_protocol": True,
                    }
                ],
                "stability_results": [{"criterion_id": "S1", "passed": True}],
                "domain_results": [
                    {"check_type": "feasibility", "passed": True}
                ],  # 优化问题的领域验证
                "passed": True,  # 校验器应忽略可选条件
                "evidence_paths": ["validation/validation.md"],
            }
        ),
        encoding="utf-8",
    )

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_validation",
        "status": "active",
        "selected_models": [
            {
                "model_id": "M1",
                "subproblem_ids": ["P1"],
                "role": "primary",
                "baseline_model_ids": ["B1"],
            },
            {"model_id": "B1", "subproblem_ids": ["P1"], "role": "baseline"},
        ],
        "runs": [
            {
                "run_id": "run-M1",
                "model_id": "M1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
            },
            {
                "run_id": "run-B1",
                "model_id": "B1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
            },
        ],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_validation", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    # 可选条件 C2 失败，但整体应通过
    assert output["passed"] is True, f"可选条件失败不应影响整体: {output.get('invalid', [])}"


# ============================================================
# 完整成功流程测试（新增）
# ============================================================


def test_full_success_flow_with_validation(tmp_path: Path) -> None:
    """完整成功流程：验证计划 + 主模型 + 基线 + 统一验证."""
    (tmp_path / "validation").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs" / "run-M1.log").write_text("log-M1", encoding="utf-8")
    (tmp_path / "runs" / "run-M1.json").write_text("{}", encoding="utf-8")
    (tmp_path / "runs" / "run-B1.log").write_text("log-B1", encoding="utf-8")
    (tmp_path / "runs" / "run-B1.json").write_text("{}", encoding="utf-8")
    (tmp_path / "validation" / "validation.md").write_text("# 验证报告", encoding="utf-8")
    (tmp_path / "validation" / "comparison.md").write_text("# 对比报告", encoding="utf-8")

    plan_path = tmp_path / "validation" / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "plan_id": "VP1",
                "primary_model_ids": ["M1"],
                "baseline_model_ids": ["B1"],
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
                "criteria": [
                    {
                        "criterion_id": "C1",
                        "metric": "rmse",
                        "direction": "minimize",
                        "operator": "<=",
                        "threshold": 10.0,
                        "source": "赛题要求",
                        "required": True,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    validation_path = tmp_path / "validation" / "validation.json"
    validation_path.write_text(
        json.dumps(
            {
                "validation_id": "V1",
                "protocol_hash": "sha256:abc123",
                "primary_model_ids": ["M1"],
                "baseline_model_ids": ["B1"],
                "run_ids": ["run-M1", "run-B1"],
                "evaluations": [
                    {"model_id": "M1", "metrics": {"rmse": 8.2}},
                    {"model_id": "B1", "metrics": {"rmse": 11.6}},
                ],
                "criteria_results": [
                    {"criterion_id": "C1", "observed": 8.2, "passed": True, "required": True}
                ],
                "comparisons": [
                    {
                        "metric": "rmse",
                        "primary_model_id": "M1",
                        "baseline_model_id": "B1",
                        "primary_value": 8.2,
                        "baseline_value": 11.6,
                        "absolute_delta": -3.4,
                        "relative_improvement": 0.29,
                        "same_protocol": True,
                    }
                ],
                "stability_results": [{"criterion_id": "S1", "passed": True}],
                "domain_results": [{"check_type": "feasibility", "passed": True}],
                "passed": True,
                "evidence_paths": ["validation/validation.md", "validation/comparison.md"],
            }
        ),
        encoding="utf-8",
    )

    index_path = tmp_path / "modeling" / "index.json"
    index = {
        "schema_version": 2,
        "project": {"type": "math-modeling", "problem_type": ["optimization"]},
        "current_phase": "model_validation",
        "status": "active",
        "selected_models": [
            {
                "model_id": "M1",
                "subproblem_ids": ["P1"],
                "role": "primary",
                "baseline_model_ids": ["B1"],
            },
            {"model_id": "B1", "subproblem_ids": ["P1"], "role": "baseline"},
        ],
        "runs": [
            {
                "run_id": "run-M1",
                "model_id": "M1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
                "command": "python run_M1.py",
                "log_paths": ["runs/run-M1.log"],
                "result_paths": ["runs/run-M1.json"],
            },
            {
                "run_id": "run-B1",
                "model_id": "B1",
                "status": "succeeded",
                "run_scope": "full",
                "protocol_hash": "sha256:abc123",
                "dataset_split_id": "split-001",
                "command": "python run_B1.py",
                "log_paths": ["runs/run-B1.log"],
                "result_paths": ["runs/run-B1.json"],
            },
        ],
        "validations": [{"validation_id": "V1", "primary_model_ids": ["M1"], "passed": False}],
        "phase_gates": {},
        "completion_audit": {"passed": False, "evidence": [], "missing_items": []},
    }
    (tmp_path / "modeling").mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index), encoding="utf-8")

    result = run_validate(tmp_path, "--phase", "model_validation", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    output = json.loads(result.stdout)
    assert output["passed"] is True, (
        f"完整验证流程应通过: {output.get('invalid', [])}, missing: {output.get('missing', [])}"
    )

    # 验证写回的 validation.json
    persisted = json.loads(validation_path.read_text(encoding="utf-8"))
    assert persisted["criteria_passed"] is True, "criteria_passed 应为 True"
    assert persisted["comparison_passed"] is True, "comparison_passed 应为 True"
    assert persisted["stability_passed"] is True, "stability_passed 应为 True"
    assert persisted["domain_checks_passed"] is True, "domain_checks_passed 应为 True"
    assert persisted["passed"] is True, "整体 passed 应为 True"


def test_json_output_valid(tmp_path: Path) -> None:
    """--json 输出必须是有效的 JSON."""
    result = run_validate(tmp_path, "--phase", "intake", "--json")
    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
    # 应该能解析
    output = json.loads(result.stdout)
    assert "passed" in output
    assert "phase" in output


# ============================================================
# 主函数（直接运行时执行所有测试）
# ============================================================


if __name__ == "__main__":
    import tempfile

    tests = [
        ("frontmatter 可解析", test_skill_frontmatter_parsable, False),
        ("reference 文件存在", test_skill_references_exist, False),
        ("所有阶段处理器", test_all_phases_have_handlers, False),
        ("未知阶段退出码", test_unknown_phase_exits_2, True),
        ("--all 执行所有阶段", test_all_checks_all_phases, True),
        ("--all 失败传递", test_all_fails_on_first_failure, True),
        ("JSON 输出可解析", test_json_output_parseable, True),
        ("--json 输出有效", test_json_output_valid, True),
        ("仅 Markdown 失败", test_final_audit_fails_with_only_markdown, True),
        ("无效 DOCX 失败", test_invalid_docx_format_fails, True),
        ("PDF 解析库检查", test_pdf_requires_parser_library, True),
        ("项目外路径拒绝", test_outside_project_path_rejected, True),
        ("只读验证", test_readonly_validation_no_changes, True),
        ("验证计划拒绝空 criteria", test_validation_plan_rejects_empty_criteria, True),
        ("验证计划拒绝缺少字段", test_validation_plan_rejects_missing_threshold_source, True),
        ("验证拒绝无基线", test_validation_rejects_missing_baseline_without_exemption, True),
        ("有效基线豁免通过", test_valid_baseline_exemption_passes, True),
        ("无效基线豁免失败", test_invalid_baseline_exemption_missing_reason_fails, True),
        ("主模型缺少运行", test_missing_primary_run_fails, True),
        ("基线模型缺少运行", test_missing_baseline_run_fails, True),
        ("协议哈希不一致", test_protocol_hash_mismatch_fails, True),
        ("数据集划分不一致", test_dataset_split_mismatch_fails, True),
        ("缺少对比指标", test_missing_comparison_fails, True),
        ("缺少稳定性检查", test_missing_stability_fails, True),
        ("生物领域验证", test_domain_validation_required_for_biological, True),
        ("多主模型支持", test_multi_primary_models_supported, True),
        ("输入变化门禁失效", test_gate_invalidation_on_input_change, True),
        ("门禁路径逃逸", test_outside_path_in_gate_invalidation_rejected, True),
        ("可选条件失败", test_optional_criteria_failure_allows_pass, True),
        ("完整验证流程", test_full_success_flow_with_validation, True),
    ]

    passed = 0
    failed = 0

    for name, test_fn, needs_tmp in tests:
        if needs_tmp:
            tmp = Path(tempfile.mkdtemp())
            try:
                test_fn(tmp)
                print(f"[PASS] {name}")
                passed += 1
            except Exception as e:
                print(f"[FAIL] {name}: {e}")
                failed += 1
        else:
            try:
                test_fn()
                print(f"[PASS] {name}")
                passed += 1
            except Exception as e:
                print(f"[FAIL] {name}: {e}")
                failed += 1

    print(f"\n总计: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)
