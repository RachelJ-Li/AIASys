"""数学建模项目校验脚本。

检查流程门禁、状态结构、证据链和完整性。
支持 --phase 单个阶段、--all 全量检查。

退出码：
  0  校验通过
  1  流程门禁未通过
  2  配置或状态文件错误
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

os_environ = os.environ

# 占位标记（必须与 init_project.py 保持一致）
_PLACEHOLDER_MARKERS = [
    "[在此粘贴赛题内容]",
    "[记录格式、篇幅、截止时间等]",
    "[记录假设、限制、工具规则等]",
    "[待填写]",
]

# 十一流程顺序（包含 paper_build）
_PHASE_ORDER = [
    "intake",
    "problem_analysis",
    "literature_research",
    "model_design",
    "model_establishment",
    "model_solving",
    "model_validation",
    "result_interpretation",
    "paper_writing",
    "paper_build",
    "final_audit",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    try:
        h.update(path.read_bytes())
        return f"sha256:{h.hexdigest()}"
    except Exception:
        return None


def _resolve_project_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    env_root = os_environ.get("AIASYS_WORKSPACE_ROOT")
    if not env_root:
        raise ValueError("未指定 --project-root 且 AIASYS_WORKSPACE_ROOT 未设置")
    return Path(env_root).resolve()


def _load_index(root: Path) -> tuple[dict | None, str | None]:
    """加载 modeling/index.json，返回 (data, error)。"""
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


def _load_index_safe(root: Path) -> tuple[dict | None, str | None]:
    """安全加载 modeling/index.json，使用路径安全检查。"""
    index_path, err = _safe_resolve_path(root, "modeling/index.json")
    if err:
        return None, f"路径无效: modeling/index.json ({err})"
    if not index_path or not index_path.exists():
        return None, "状态文件不存在: modeling/index.json"
    try:
        raw = index_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None, "状态文件内容不是对象"
        return data, None
    except json.JSONDecodeError as exc:
        return None, f"状态文件 JSON 解析失败: {exc}"


def _check_file_exists(root: Path, rel_path: str, missing: list[str], warnings: list[str]) -> None:
    """检查文件是否存在，使用统一的安全路径解析。"""
    target, err = _safe_resolve_path(root, rel_path)
    if err:
        missing.append(f"路径无效（已拒绝）: {rel_path}")
        return
    if not target.exists():
        missing.append(rel_path)
    elif target.stat().st_size == 0:
        warnings.append(f"文件为空: {rel_path}")


def _is_placeholder(content: str) -> bool:
    """检查内容是否包含占位标记。"""
    return any(marker in content for marker in _PLACEHOLDER_MARKERS)


def _check_placeholder(root: Path, rel_path: str, invalid: list[str]) -> bool:
    """检查文件是否为占位内容。返回 True 如果是占位内容。"""
    target = root / rel_path
    if not target.exists():
        return False
    content = target.read_text(encoding="utf-8")
    return _is_placeholder(content)


def _check_phase_intake(root: Path, index: dict) -> dict:
    """阶段 1：材料接收与规则核验。"""
    result = {
        "phase": "intake",
        "passed": False,
        "missing": [],
        "invalid": [],
        "warnings": [],
        "next_action": "",
        "requires_user": False,
    }
    missing, invalid = result["missing"], result["invalid"]

    # 必需文件
    for rel in ["statement/problem.md", "statement/requirements.md", "statement/constraints.md"]:
        target, err = _safe_resolve_path(root, rel)
        if err:
            invalid.append(f"路径无效: {rel}")
            continue
        if not target or not target.exists():
            missing.append(rel)
        elif target.stat().st_size == 0:
            invalid.append(f"文件为空: {rel}")
        elif _is_placeholder(target.read_text(encoding="utf-8")):
            invalid.append(f"文件仍为占位内容: {rel}")

    # 状态字段
    project = index.get("project", {})
    if not project.get("type"):
        invalid.append("project.type 未填写")
    if not project.get("problem_type"):
        invalid.append("project.problem_type 未填写")
    rp = index.get("research_policy", {})
    if not rp.get("rules_checked"):
        invalid.append("research_policy.rules_checked 未设置为 true")

    result["passed"] = len(missing) == 0 and len(invalid) == 0
    if not result["passed"]:
        result["next_action"] = "补充 statement/ 文件并填写项目信息"
    return result


def _check_phase_problem_analysis(root: Path, index: dict) -> dict:
    """阶段 2：问题理解与拆解。"""
    result = {
        "phase": "problem_analysis",
        "passed": False,
        "missing": [],
        "invalid": [],
        "warnings": [],
        "next_action": "",
        "requires_user": False,
    }
    missing, invalid, warnings = result["missing"], result["invalid"], result["warnings"]

    _check_file_exists(root, "analysis/problem_analysis.md", missing, warnings)
    _check_file_exists(root, "analysis/data_profile.md", missing, warnings)

    # 检查是否为占位内容
    if _check_placeholder(root, "analysis/problem_analysis.md", invalid):
        invalid.append("analysis/problem_analysis.md 仍为占位内容")
    if _check_placeholder(root, "analysis/data_profile.md", invalid):
        invalid.append("analysis/data_profile.md 仍为占位内容")

    subproblems = index.get("subproblems", [])
    if not subproblems:
        invalid.append("subproblems 为空")

    result["passed"] = len(missing) == 0 and len(invalid) == 0
    if not result["passed"]:
        result["next_action"] = "创建 problem_analysis.md 和 data_profile.md"
    return result


def _check_phase_literature_research(root: Path, index: dict) -> dict:
    """阶段 3：文献与资料检索。"""
    result = {
        "phase": "literature_research",
        "passed": False,
        "missing": [],
        "invalid": [],
        "warnings": [],
        "next_action": "",
        "requires_user": False,
    }
    missing, invalid, warnings = result["missing"], result["invalid"], result["warnings"]

    _check_file_exists(root, "research/references.json", missing, warnings)
    refs = index.get("references", [])
    if not refs:
        invalid.append("references 为空")

    result["passed"] = len(missing) == 0 and len(invalid) == 0
    if not result["passed"]:
        result["next_action"] = "创建 research/references.json"
    return result


def _check_phase_model_design(root: Path, index: dict) -> dict:
    """阶段 4：假设、符号与模型选择。"""
    result = {
        "phase": "model_design",
        "passed": False,
        "missing": [],
        "invalid": [],
        "warnings": [],
        "next_action": "",
        "requires_user": False,
    }
    missing, invalid = result["missing"], result["invalid"]

    # 检查基本文件
    for rel in ["model/assumptions.md", "model/notation.md", "model/selection.md"]:
        _check_file_exists(root, rel, missing, result["warnings"])
        if _check_placeholder(root, rel, invalid):
            invalid.append(f"{rel} 仍为占位内容")

    # 检查 selected_models
    selected_models = index.get("selected_models", [])
    if not selected_models:
        invalid.append("selected_models 为空")
        result["passed"] = False
        result["next_action"] = "创建模型选择文件并填写 selected_models"
        return result

    # 检查每个主模型有 role 字段
    for model in selected_models:
        if "role" not in model:
            invalid.append(f"模型 {model.get('model_id')} 缺少 role 字段")

    # 检查基线要求
    baseline_ok, baseline_issues = _check_baseline_requirement(root, selected_models, index)
    invalid.extend(baseline_issues)

    result["passed"] = len(missing) == 0 and len(invalid) == 0
    if not result["passed"]:
        result["next_action"] = "完成模型选择并设置基线"
    return result


def _check_phase_model_establishment(root: Path, index: dict) -> dict:
    """阶段 5：模型建立。"""
    result = {
        "phase": "model_establishment",
        "passed": False,
        "missing": [],
        "invalid": [],
        "warnings": [],
        "next_action": "",
        "requires_user": False,
    }
    missing, invalid = result["missing"], result["invalid"]

    selected_models = index.get("selected_models", [])
    if not selected_models:
        invalid.append("selected_models 为空，无法建立模型")
        result["passed"] = False
        result["next_action"] = "先完成模型选择"
        return result

    # 检查每个选定模型的 formulation 和 algorithm
    for model in selected_models:
        model_id = model.get("model_id", "unknown")
        fmt_path = model.get("formulation_path", f"model/{model_id}/formulation.md")
        alg_path = model.get("algorithm_path", f"model/{model_id}/algorithm.md")

        _check_file_exists(root, fmt_path, missing, result["warnings"])
        _check_file_exists(root, alg_path, missing, result["warnings"])

        if _check_placeholder(root, fmt_path, invalid):
            invalid.append(f"{fmt_path} 仍为占位内容")
        if _check_placeholder(root, alg_path, invalid):
            invalid.append(f"{alg_path} 仍为占位内容")

    # 检查 validation/plan.json
    plan_path = "validation/plan.json"
    plan = _check_validation_plan(root, plan_path, missing, invalid)
    if plan:
        # 验证计划存在且基本有效，检查主模型和基线是否存在
        primary_ids = plan.get("primary_model_ids", [])
        baseline_ids = plan.get("baseline_model_ids", [])

        existing_model_ids = {m.get("model_id") for m in selected_models}
        for pid in primary_ids:
            if pid not in existing_model_ids:
                invalid.append(f"验证计划中的主模型 {pid} 不在 selected_models 中")
        for bid in baseline_ids:
            if bid not in existing_model_ids:
                invalid.append(f"验证计划中的基线模型 {bid} 不在 selected_models 中")

    result["passed"] = len(missing) == 0 and len(invalid) == 0
    if not result["passed"]:
        result["next_action"] = "为每个选定模型建立 formulation.md 和 algorithm.md，并创建验证计划"
    return result


def _validate_path_in_project(root: Path, path: str) -> tuple[bool, str]:
    """验证路径是否在项目内，返回 (valid, error)。"""
    try:
        resolved = (root / path).resolve()
        resolved.relative_to(root)
        return True, ""
    except (ValueError, OSError) as e:
        return False, str(e)


def _safe_resolve_path(root: Path, rel_path: str) -> tuple[Path | None, str | None]:
    """统一的安全路径解析函数。

    Returns:
        (resolved_path, error) 元组
        - 成功：返回 (Path, None)
        - 失败：返回 (None, error_message)
    """
    try:
        resolved = (root / rel_path).resolve()
        resolved.relative_to(root)
        return resolved, None
    except (ValueError, OSError) as e:
        return None, f"路径逃逸或无效: {rel_path} ({e})"


def _load_json_object(root: Path, rel_path: str) -> tuple[dict | None, str | None]:
    """加载 JSON 文件并验证为对象，返回 (data, error)。"""
    target, err = _safe_resolve_path(root, rel_path)
    if err:
        return None, err
    if not target or not target.exists():
        return None, f"文件不存在: {rel_path}"
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None, f"文件内容不是对象: {rel_path}"
        return data, None
    except json.JSONDecodeError as exc:
        return None, f"JSON 解析失败: {rel_path} ({exc})"


def _check_validation_plan(
    root: Path, plan_path: str, missing: list[str], invalid: list[str]
) -> dict | None:
    """检查 validation/plan.json 是否有效。返回 plan 数据或 None。"""
    plan, err = _load_json_object(root, plan_path)
    if err:
        invalid.append(f"验证计划加载失败: {err}")
        return None

    # 检查必要字段
    if "criteria" not in plan:
        invalid.append("验证计划缺少 criteria 字段")
        return None
    criteria = plan.get("criteria", [])
    if not criteria:
        invalid.append("验证计划 criteria 为空")
        return None

    # 检查 primary_model_ids 和 baseline_model_ids
    if "primary_model_ids" not in plan:
        invalid.append("验证计划缺少 primary_model_ids")
    if "baseline_model_ids" not in plan:
        invalid.append("验证计划缺少 baseline_model_ids")

    # 检查每项条件
    for i, criterion in enumerate(criteria):
        cid = criterion.get("criterion_id", f"C{i + 1}")
        if "metric" not in criterion:
            invalid.append(f"条件 {cid} 缺少 metric 字段")
        if "direction" not in criterion:
            invalid.append(f"条件 {cid} 缺少 direction 字段")
        elif criterion["direction"] not in ["minimize", "maximize", "target", "boolean"]:
            invalid.append(f"条件 {cid} 的 direction 非法: {criterion['direction']}")
        if "operator" not in criterion:
            invalid.append(f"条件 {cid} 缺少 operator 字段")
        elif criterion["operator"] not in ["<", "<=", ">", ">=", "==", "between"]:
            invalid.append(f"条件 {cid} 的 operator 非法: {criterion['operator']}")
        if "threshold" not in criterion:
            invalid.append(f"条件 {cid} 缺少 threshold 字段")
        if "source" not in criterion:
            invalid.append(f"条件 {cid} 缺少 source 字段")

    return plan


def _check_evaluation_protocol(run: dict, plan_hash: str, split_id: str) -> list[str]:
    """检查运行记录是否符合统一实验协议。"""
    issues = []

    if run.get("protocol_hash") != plan_hash:
        issues.append(f"运行 {run.get('run_id')} 的 protocol_hash 与验证计划不一致")
    if run.get("dataset_split_id") != split_id:
        issues.append(f"运行 {run.get('run_id')} 的 dataset_split_id 与验证计划不一致")

    return issues


def _compare_metric(primary_value: float, baseline_value: float, metric: str) -> dict:
    """计算主模型与基线的对比结果。"""
    absolute_delta = primary_value - baseline_value
    relative_improvement = (
        (baseline_value - primary_value) / baseline_value if baseline_value != 0 else 0.0
    )

    return {
        "metric": metric,
        "primary_value": primary_value,
        "baseline_value": baseline_value,
        "absolute_delta": absolute_delta,
        "relative_improvement": relative_improvement,
        "same_protocol": True,  # 由调用方判断
    }


def _compute_criteria_results(criteria: list[dict], evaluations: list[dict]) -> list[dict]:
    """根据 evaluations 计算各条件的通过状态。

    Args:
        criteria: 验证条件列表
        evaluations: 评估结果数组，每个元素包含 model_id 和 metrics

    Returns:
        条件结果列表，每个包含 criterion_id、observed、passed、required
    """
    results = []
    for criterion in criteria:
        cid = criterion.get("criterion_id", "")
        metric = criterion.get("metric", "")
        operator = criterion.get("operator", "==")
        threshold = criterion.get("threshold")
        required = criterion.get("required", True)

        # 从 evaluations 数组中提取指标值
        observed = None
        if isinstance(evaluations, list):
            # evaluations 是数组格式：[{model_id, metrics: {metric: value}}]
            for eval_item in evaluations:
                if isinstance(eval_item, dict) and "metrics" in eval_item:
                    eval_metrics = eval_item.get("metrics", {})
                    if metric in eval_metrics:
                        observed = eval_metrics[metric]
                        break
        elif isinstance(evaluations, dict):
            # 兼容旧格式：直接是 {metric: value} 字典
            observed = evaluations.get(metric)

        if observed is None:
            results.append(
                {
                    "criterion_id": cid,
                    "observed": None,
                    "passed": False,
                    "required": required,
                    "reason": f"缺少指标 {metric}",
                }
            )
            continue

        # 根据 operator 判断是否通过
        passed = False
        if operator == "<":
            passed = observed < threshold
        elif operator == "<=":
            passed = observed <= threshold
        elif operator == ">":
            passed = observed > threshold
        elif operator == ">=":
            passed = observed >= threshold
        elif operator == "==":
            passed = observed == threshold
        elif operator == "between":
            if isinstance(threshold, list) and len(threshold) == 2:
                passed = threshold[0] <= observed <= threshold[1]

        results.append(
            {
                "criterion_id": cid,
                "observed": observed,
                "passed": passed,
                "required": required,
            }
        )

    return results


def _check_comparable_runs(
    root: Path, primary_ids: list[str], baseline_ids: list[str], plan_hash: str, split_id: str
) -> list[str]:
    """检查主模型和基线的运行是否可比。支持多主模型和多基线。"""
    issues = []
    index, err = _load_index_safe(root)
    if err or not index:
        return [f"无法加载 index: {err}"]

    runs = index.get("runs", [])

    # 检查所有主模型
    for pid in primary_ids:
        primary_runs = [
            r
            for r in runs
            if r.get("model_id") == pid
            and r.get("status") == "succeeded"
            and r.get("run_scope") == "full"
        ]
        if not primary_runs:
            issues.append(f"主模型 {pid} 缺少成功全量运行")

        # 检查协议一致性
        for run in primary_runs:
            run_issues = _check_evaluation_protocol(run, plan_hash, split_id)
            issues.extend(run_issues)

    # 检查所有基线模型
    for bid in baseline_ids:
        baseline_runs = [
            r
            for r in runs
            if r.get("model_id") == bid
            and r.get("status") == "succeeded"
            and r.get("run_scope") == "full"
        ]
        if not baseline_runs:
            issues.append(f"基线模型 {bid} 缺少成功全量运行")

        # 检查协议一致性
        for run in baseline_runs:
            run_issues = _check_evaluation_protocol(run, plan_hash, split_id)
            issues.extend(run_issues)

    return issues


def _check_baseline_requirement(
    root: Path, selected_models: list[dict], index: dict
) -> tuple[bool, list[str]]:
    """检查基线要求：每个主模型必须有基线或有效豁免。返回 (通过, 问题列表)。"""
    issues = []

    primary_models = [m for m in selected_models if m.get("role") == "primary"]
    if not primary_models:
        return True, []  # 没有主模型，跳过检查

    for model in primary_models:
        model_id = model.get("model_id", "unknown")
        baseline_ids = model.get("baseline_model_ids", [])

        if not baseline_ids:
            # 检查是否有基线豁免
            exemption = model.get("baseline_exemption")
            if not exemption:
                issues.append(
                    f"主模型 {model_id} 缺少基线模型（应在 selected_models 中添加 baseline_model_ids 或登记基线豁免 baseline_exemption）"
                )
            else:
                # 验证豁免信息是否完整
                reason = exemption.get("reason", "")
                alternative = exemption.get("alternative", "")
                evidence_paths = exemption.get("evidence_paths", [])

                if not reason:
                    issues.append(f"主模型 {model_id} 的基线豁免缺少 reason")
                if not alternative:
                    issues.append(f"主模型 {model_id} 的基线豁免缺少 alternative")
                if not evidence_paths:
                    issues.append(f"主模型 {model_id} 的基线豁免缺少 evidence_paths")
                else:
                    # 验证证据路径是否存在
                    for ep in evidence_paths:
                        target, err = _safe_resolve_path(root, ep)
                        if err:
                            issues.append(f"主模型 {model_id} 的基线豁免证据路径无效: {ep}")
                        elif not target or not target.exists():
                            issues.append(f"主模型 {model_id} 的基线豁免证据文件不存在: {ep}")

    return len(issues) == 0, issues


def _check_stability_results(root: Path, validation_json: dict) -> tuple[bool, list[str]]:
    """检查稳定性验证结果。"""
    stability = validation_json.get("stability_results", [])
    if not stability:
        return False, ["稳定性验证结果为空"]

    # 检查是否有失败项
    failed = [s for s in stability if not s.get("passed", False)]
    if failed:
        return False, [f"稳定性检查失败: {s.get('criterion_id', 'unknown')}" for s in failed]

    return True, []


def _check_domain_results(
    root: Path, validation_json: dict, problem_types: list[str]
) -> tuple[bool, list[str]]:
    """检查领域验证结果。"""
    domain_results = validation_json.get("domain_results", [])
    issues = []

    if not domain_results:
        # 检查问题类型是否要求领域验证
        # 根据 validation-profiles.md，以下问题类型需要领域验证
        domain_required_types = {
            "optimization": ["feasibility", "objective_value", "convergence"],
            "regression": ["mae", "rmse", "mape", "r_squared", "cross_validation"],
            "classification": ["precision", "recall", "f1", "roc_auc", "confusion_matrix"],
            "time_series": ["rolling_validation", "prediction_error", "residual_autocorrelation"],
            "clustering": ["silhouette_coefficient", "cluster_stability"],
            "ode": ["numerical_convergence", "conservation_laws", "analytical_comparison"],
            "biological": [
                "statistical_significance",
                "multiple_testing_correction",
                "biological_plausibility",
            ],
        }

        # 检查是否有任何问题类型要求领域验证
        requires_domain = False
        for pt in problem_types:
            if pt in domain_required_types:
                requires_domain = True
                break

        if requires_domain:
            return False, [f"问题类型 {problem_types} 需要领域验证，但 domain_results 为空"]

        return True, []

    # 检查是否有失败项
    failed = [d for d in domain_results if not d.get("passed", False)]
    if failed:
        return False, [f"领域检查失败: {d.get('check_type', 'unknown')}" for d in failed]

    return True, issues


def _compute_validation_passed(validation_json: dict) -> bool:
    """根据 validation.json 计算整体验证通过状态。"""
    # 必须由校验器计算，不允许直接读取 validation_json["passed"]
    criteria_results = validation_json.get("criteria_results", [])
    comparison_passed = validation_json.get("comparison_passed", False)
    stability_passed = validation_json.get("stability_passed", False)
    domain_checks_passed = validation_json.get("domain_checks_passed", True)

    # 所有 required criteria 必须通过
    required_criteria = [c for c in criteria_results if c.get("required", True)]
    all_criteria_passed = all(c.get("passed", False) for c in required_criteria)

    return all_criteria_passed and comparison_passed and stability_passed and domain_checks_passed


def _check_phase_model_solving(root: Path, index: dict) -> dict:
    """阶段 6：编程求解与数值实验。"""
    result = {
        "phase": "model_solving",
        "passed": False,
        "missing": [],
        "invalid": [],
        "warnings": [],
        "next_action": "",
        "requires_user": False,
    }
    missing, invalid, warnings = result["missing"], result["invalid"], result["warnings"]

    # 检查 runs 是否有成功运行
    runs = index.get("runs", [])
    if not runs:
        missing.append("runs 为空（模型未运行）")
        result["passed"] = False
        result["next_action"] = "运行模型并登记到 runs/"
        return result

    # 检查验证计划
    plan, plan_err = _load_json_object(root, "validation/plan.json")
    if plan_err:
        invalid.append(f"验证计划不可用: {plan_err}")
        # 不立即返回，继续检查运行记录

    # 检查最小运行门禁
    min_runs = [
        r for r in runs if r.get("run_scope") == "minimum" and r.get("status") == "succeeded"
    ]
    if not min_runs:
        missing.append("缺少通过最小运行门禁的记录（run_scope=minimum 且 status=succeeded）")
    else:
        # 检查 minimum_gate_passed
        for run in min_runs:
            if not run.get("minimum_gate_passed"):
                invalid.append(
                    f"最小运行 {run.get('run_id')} 未通过门禁（minimum_gate_passed=false）"
                )

    if plan:
        protocol_hash = plan.get("protocol_hash", "")
        split_id = plan.get("dataset_split_id", "")
        primary_ids = plan.get("primary_model_ids", [])
        baseline_ids = plan.get("baseline_model_ids", [])

        # 检查主模型运行
        for pid in primary_ids:
            primary_full_runs = [
                r
                for r in runs
                if r.get("model_id") == pid
                and r.get("run_scope") == "full"
                and r.get("status") == "succeeded"
            ]
            if not primary_full_runs:
                invalid.append(f"主模型 {pid} 缺少成功全量运行")

        # 检查基线运行
        for bid in baseline_ids:
            baseline_full_runs = [
                r
                for r in runs
                if r.get("model_id") == bid
                and r.get("run_scope") == "full"
                and r.get("status") == "succeeded"
            ]
            if not baseline_full_runs:
                invalid.append(f"基线模型 {bid} 缺少成功全量运行")

        # 检查协议一致性（支持多模型对比）
        comparable_issues = _check_comparable_runs(
            root, primary_ids, baseline_ids, protocol_hash, split_id
        )
        invalid.extend(comparable_issues)

    # 检查运行记录完整性
    success_runs = [r for r in runs if r.get("status") == "succeeded"]
    for run in success_runs:
        run_id = run.get("run_id", "unknown")

        # 检查命令
        if not run.get("command"):
            invalid.append(f"运行 {run_id} 缺少 command 字段")

        # random_seed = 0 是合法的
        if "random_seed" not in run:
            warnings.append(f"运行 {run_id} 缺少 random_seed 字段")

        # 检查日志
        log_paths = run.get("log_paths", [])
        if not log_paths:
            invalid.append(f"运行 {run_id} 无日志路径")
        else:
            for lp in log_paths:
                target, err = _safe_resolve_path(root, lp)
                if err:
                    invalid.append(f"运行 {run_id} 日志路径无效: {lp}")
                    continue
                if not target or not target.exists():
                    invalid.append(f"日志文件不存在: {lp}")
                elif target.stat().st_size == 0:
                    warnings.append(f"日志文件为空: {lp}")

        # 检查结果
        result_paths = run.get("result_paths", [])
        if not result_paths:
            invalid.append(f"运行 {run_id} 无结果路径")
        else:
            for rp in result_paths:
                target, err = _safe_resolve_path(root, rp)
                if err:
                    invalid.append(f"运行 {run_id} 结果路径无效: {rp}")
                    continue
                if not target or not target.exists():
                    invalid.append(f"结果文件不存在: {rp}")
                elif target.stat().st_size == 0:
                    warnings.append(f"结果文件为空: {rp}")

        # 检查 reproduce_command
        if not run.get("reproduce_command"):
            warnings.append(f"运行 {run_id} 缺少 reproduce_command")

    result["passed"] = len(invalid) == 0
    if not result["passed"]:
        result["next_action"] = "完成最小运行门禁并执行主模型和基线模型"
    return result


def _check_phase_model_validation(root: Path, index: dict) -> dict:
    """阶段 7：模型检验。"""
    result = {
        "phase": "model_validation",
        "passed": False,
        "missing": [],
        "invalid": [],
        "warnings": [],
        "next_action": "",
        "requires_user": False,
    }
    invalid = result["invalid"]
    warnings = result.setdefault("warnings", [])

    # 1. 检查验证计划
    plan, plan_err = _load_json_object(root, "validation/plan.json")
    if plan_err:
        invalid.append(f"验证计划不可用: {plan_err}")
        result["passed"] = False
        result["next_action"] = "创建验证计划 validation/plan.json"
        return result

    # 2. 检查验证结果
    validation_json, val_err = _load_json_object(root, "validation/validation.json")
    if val_err:
        invalid.append(f"验证结果不可用: {val_err}")
        result["passed"] = False
        result["next_action"] = "运行验证并生成 validation/validation.json"
        return result

    # 3. 检查协议一致性
    protocol_hash = plan.get("protocol_hash", "")
    split_id = plan.get("dataset_split_id", "")
    if not protocol_hash or not split_id:
        invalid.append("验证计划缺少 protocol_hash 或 dataset_split_id")

    # 4. 根据验证计划和实际指标计算各条件的通过状态
    primary_model_ids = plan.get("primary_model_ids", [])

    # 从 evaluations 数组中提取主模型指标
    evaluations = validation_json.get("evaluations", [])
    primary_metrics = {}
    if isinstance(evaluations, list):
        for eval_item in evaluations:
            if isinstance(eval_item, dict):
                model_id = eval_item.get("model_id")
                metrics = eval_item.get("metrics", {})
                if model_id and model_id in primary_model_ids:
                    primary_metrics.update(metrics)

    # 根据实际指标重新生成 criteria_results
    computed_criteria = _compute_criteria_results(plan.get("criteria", []), evaluations)
    failed_criteria = [
        c for c in computed_criteria if not c.get("passed", False) and c.get("required", True)
    ]
    if failed_criteria:
        invalid.append(f"必要条件未通过: {[c.get('criterion_id') for c in failed_criteria]}")

    # 更新 validation_json 中的 criteria_results
    validation_json["criteria_results"] = computed_criteria
    criteria_passed = len(failed_criteria) == 0
    validation_json["criteria_passed"] = criteria_passed

    # 5. 完善对比验证：检查必需字段并从 evaluations 重新计算对比数值
    comparisons = validation_json.get("comparisons", [])
    comparison_passed = True
    if not comparisons:
        invalid.append("验证结果缺少 comparisons")
    else:
        for comp in comparisons:
            # 检查必需字段
            required_fields = [
                "metric",
                "primary_model_id",
                "baseline_model_id",
                "primary_value",
                "baseline_value",
                "absolute_delta",
                "relative_improvement",
                "same_protocol",
            ]
            missing_fields = [f for f in required_fields if f not in comp]
            if missing_fields:
                invalid.append(f"对比项缺少必需字段: {missing_fields}")
                comparison_passed = False

            # 检查 same_protocol 字段
            if not comp.get("same_protocol"):
                comparison_passed = False
                invalid.append(f"对比指标 {comp.get('metric')} 的协议不一致")

    validation_json["comparison_passed"] = comparison_passed

    # 6. 检查稳定性
    stability_ok, stability_issues = _check_stability_results(root, validation_json)
    validation_json["stability_passed"] = stability_ok
    if not stability_ok:
        invalid.extend(stability_issues)

    # 7. 检查领域验证
    problem_types = index.get("project", {}).get("problem_type", [])
    domain_ok, domain_issues = _check_domain_results(root, validation_json, problem_types)
    validation_json["domain_checks_passed"] = domain_ok
    if not domain_ok:
        invalid.extend(domain_issues)

    # 8. 计算整体通过状态
    computed_passed = _compute_validation_passed(validation_json)

    # 9. 检查证据文件
    evidence_paths = validation_json.get("evidence_paths", [])
    for ep in evidence_paths:
        target, err = _safe_resolve_path(root, ep)
        if err:
            invalid.append(f"证据路径无效: {ep}")
        elif not target or not target.exists():
            invalid.append(f"证据文件不存在: {ep}")

    # 10. 更新 validation_json 中的通过状态
    validation_json["passed"] = computed_passed

    # 11. 如果 --record，写回 validation/validation.json
    validation_json_path = root / "validation" / "validation.json"
    if validation_json_path.exists():
        try:
            _write_json(validation_json_path, validation_json)
        except Exception as e:
            warnings.append(f"无法写入 validation.json: {e}")

    # 12. 验证通过条件：所有检查通过且计算结果为通过
    result["passed"] = len(invalid) == 0 and computed_passed
    if not result["passed"]:
        result["next_action"] = "修复验证问题并重新运行验证"
    else:
        result["next_action"] = "验证通过，可以进入结果解释阶段"

    return result


def _check_phase_result_interpretation(root: Path, index: dict) -> dict:
    """阶段 8：结果解释与可视化。"""
    result = {
        "phase": "result_interpretation",
        "passed": False,
        "missing": [],
        "invalid": [],
        "warnings": [],
        "next_action": "",
        "requires_user": False,
    }
    missing, invalid, warnings = result["missing"], result["invalid"], result["warnings"]

    _check_file_exists(root, "results/summary.md", missing, warnings)
    if _check_placeholder(root, "results/summary.md", invalid):
        invalid.append("results/summary.md 仍为占位内容")

    # 检查是否有通过的有效检验
    validations = index.get("validations", [])
    passed_vals = [v for v in validations if v.get("passed")]
    if not passed_vals:
        warnings.append("尚无通过的有效检验")

    result["passed"] = len(missing) == 0 and len(invalid) == 0
    if not result["passed"]:
        result["next_action"] = "创建 results/summary.md"
    return result


def _check_phase_paper_writing(root: Path, index: dict) -> dict:
    """阶段 9：Markdown 文章撰写。只检查 Markdown 交付物。"""
    result = {
        "phase": "paper_writing",
        "passed": False,
        "missing": [],
        "invalid": [],
        "warnings": [],
        "next_action": "",
        "requires_user": False,
    }
    missing, invalid, warnings = result["missing"], result["invalid"], result["warnings"]

    _check_file_exists(root, "paper/outline.md", missing, warnings)
    _check_file_exists(root, "paper/final.md", missing, warnings)
    _check_file_exists(root, "paper/references.md", missing, warnings)

    if _check_placeholder(root, "paper/outline.md", invalid):
        invalid.append("paper/outline.md 仍为占位内容")
    if _check_placeholder(root, "paper/final.md", invalid):
        invalid.append("paper/final.md 仍为占位内容")

    # 检查大纲中的主张—证据映射
    outline_path = root / "paper" / "outline.md"
    if outline_path.exists():
        content = outline_path.read_text(encoding="utf-8")
        if "运行结果" not in content and "图表" not in content:
            warnings.append("paper/outline.md 缺少主张—证据映射")

    result["passed"] = len(missing) == 0 and len(invalid) == 0
    if not result["passed"]:
        result["next_action"] = "完成论文大纲和正文"
    return result


def _check_docx_valid(root: Path, docx_path: str) -> tuple[bool, str]:
    """检查 DOCX 是否为有效的 OOXML（ZIP）格式并包含非空正文。"""
    import zipfile

    docx_file, docx_err = _safe_resolve_path(root, docx_path)
    if docx_err:
        return False, f"DOCX 路径无效: {docx_err}"

    if not docx_file or not docx_file.exists():
        return False, f"DOCX 不存在: {docx_path}"

    # 检查是否为有效的 ZIP 文件（OOXML 基于 ZIP）
    try:
        with zipfile.ZipFile(docx_file, "r") as zf:
            # 检查是否包含 OOXML 必需的 [Content_Types].xml
            if "[Content_Types].xml" not in zf.namelist():
                return False, f"DOCX 缺少 [Content_Types].xml: {docx_path}"

            # 检查是否包含 word/document.xml（真实 DOCX 的核心文件）
            if "word/document.xml" not in zf.namelist():
                return False, f"DOCX 缺少 word/document.xml: {docx_path}"

            # 验证 [Content_Types].xml 内容
            try:
                content_types = zf.read("[Content_Types].xml").decode("utf-8")
                if (
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
                    not in content_types
                ):
                    return False, f"DOCX Content Types 未声明 Word 文档类型: {docx_path}"
            except Exception as e:
                return False, f"DOCX [Content_Types].xml 解析失败: {docx_path} ({e})"

            # 验证 word/document.xml 可解析且包含非空正文
            try:
                doc_xml = zf.read("word/document.xml").decode("utf-8")
                if not doc_xml or len(doc_xml.strip()) == 0:
                    return False, f"DOCX word/document.xml 为空: {docx_path}"

                # 基本 XML 结构检查
                if "<w:document" not in doc_xml and "<document" not in doc_xml:
                    return False, f"DOCX word/document.xml 缺少文档根元素: {docx_path}"

                # 检查是否包含 body 元素
                if "<w:body>" not in doc_xml and "<body>" not in doc_xml:
                    return False, f"DOCX word/document.xml 缺少 body 元素: {docx_path}"

                # 检查 body 是否为空（不允许空文档）
                import re

                body_match = re.search(r"<w:body[^>]*>(.*?)</w:body>", doc_xml, re.DOTALL)
                if not body_match:
                    body_match = re.search(r"<body[^>]*>(.*?)</body>", doc_xml, re.DOTALL)

                if body_match:
                    body_content = body_match.group(1).strip()
                    # 移除空白字符和 XML 标签后检查
                    text_only = re.sub(r"<[^>]+>", "", body_content).strip()
                    if not text_only:
                        return (
                            False,
                            f"DOCX word/document.xml 正文为空（不包含文本内容）: {docx_path}",
                        )
                else:
                    return False, f"DOCX word/document.xml 无法提取 body 内容: {docx_path}"

            except Exception as e:
                return False, f"DOCX word/document.xml 解析失败: {docx_path} ({e})"

        return True, ""
    except (zipfile.BadZipFile, Exception) as e:
        return False, f"DOCX 不是有效的 ZIP 格式: {docx_path} ({e})"


def _check_latex_references(root: Path, latex_dir: str) -> list[str]:
    """检查 LaTeX 项目中的引用是否有效（基础检查）。"""
    import re

    latex_root = root / latex_dir
    issues = []

    if not latex_root.exists():
        return [f"LaTeX 目录不存在: {latex_dir}"]

    main_tex = latex_root / "main.tex"
    if not main_tex.exists():
        return [f"LaTeX main.tex 不存在: {latex_dir}/main.tex"]

    content = main_tex.read_text(encoding="utf-8")

    # 检查 \input 和 \include 的文件是否存在（基础检查）
    input_pattern = re.compile(r"\\(?:input|include)\{([^}]+)\}")
    for match in input_pattern.finditer(content):
        ref_file = match.group(1)
        if not ref_file.endswith(".tex"):
            ref_file += ".tex"
        ref_path = latex_root / ref_file
        if not ref_path.exists():
            issues.append(f"LaTeX 引用的文件不存在: {latex_dir}/{ref_file}")

    # 检查 \includegraphics 的图片是否存在（基础检查）
    graphics_pattern = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
    for match in graphics_pattern.finditer(content):
        img_file = match.group(1)
        # 尝试常见图片扩展名
        found = False
        for ext in [".pdf", ".png", ".jpg", ".jpeg"]:
            img_path = latex_root / (img_file + ext)
            if img_path.exists():
                found = True
                break
        if not found:
            issues.append(f"LaTeX 引用的图片不存在: {latex_dir}/{img_file}.*")

    return issues


def _check_pdf_source(root: Path, pdf_path: str, build_json_path: str) -> tuple[bool, str]:
    """检查 PDF 是否由当前 LaTeX 构建记录生成。

    验证内容：
    - PDF 文件头必须以 %PDF 开头
    - 文件大小合理（至少 100 字节）
    - 必须可以使用 PDF 解析库打开并确认至少一页
    - 实际文件哈希与构建记录一致
    - 构建记录的 LaTeX 源码哈希与当前源码一致
    - PDF 来源记录为当前 LaTeX 项目
    """

    pdf_file, pdf_err = _safe_resolve_path(root, pdf_path)
    if pdf_err:
        return False, f"PDF 路径无效: {pdf_err}"

    if not pdf_file or not pdf_file.exists():
        return False, f"PDF 不存在: {pdf_path}"

    # 检查是否为有效 PDF（文件头必须以 %PDF 开头）
    try:
        with pdf_file.open("rb") as f:
            header = f.read(4)
            if header != b"%PDF":
                return False, f"文件不是有效的 PDF: {pdf_path}（文件头不正确）"

            # 检查文件大小（真实 PDF 至少要有几百字节）
            f.seek(0, 2)
            file_size = f.tell()
            if file_size < 100:
                return False, f"PDF 文件过小（{file_size} 字节），不像是真实编译结果: {pdf_path}"
    except Exception as e:
        return False, f"无法读取 PDF: {pdf_path} ({e})"

    # 尝试使用 pypdf 或 PyMuPDF 解析 PDF（必须成功）
    try:
        # 优先使用 pypdf
        try:
            import pypdf

            reader = pypdf.PdfReader(str(pdf_file))
            if len(reader.pages) == 0:
                return False, f"PDF 不包含任何页面: {pdf_path}"
        except ImportError:
            # 尝试 PyMuPDF
            try:
                import fitz  # PyMuPDF

                doc = fitz.open(str(pdf_file))
                if doc.page_count == 0:
                    return False, f"PDF 不包含任何页面: {pdf_path}"
                doc.close()
            except ImportError:
                # 都没有安装，返回失败
                return False, "PDF 解析库不可用（需要 pypdf 或 PyMuPDF）"
    except Exception as e:
        return False, f"PDF 解析失败（可能文件损坏）: {pdf_path} ({e})"

    # 检查构建记录
    build_json, build_err = _safe_resolve_path(root, build_json_path)
    if build_err:
        return False, f"构建记录路径无效: {build_err}"

    if not build_json or not build_json.exists():
        return False, f"构建记录不存在: {build_json_path}"

    try:
        build_data = json.loads(build_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, f"构建记录 JSON 解析失败: {build_json_path}"

    # 检查构建状态
    if build_data.get("status") != "succeeded":
        return False, f"LaTeX 构建状态非 succeeded: {build_data.get('status')}"

    # 检查 return_code 是否为 0
    return_code = build_data.get("return_code")
    if return_code is None:
        return False, "构建记录缺少 return_code 字段"
    if return_code != 0:
        return False, f"LaTeX 编译退出码非零: {return_code}"

    # 检查 LaTeX 引擎是否在允许列表中
    allowed_engines = {"xelatex", "pdflatex", "lualatex", "latexmk", "tectonic"}
    engine = build_data.get("engine", "")
    if not engine:
        return False, "构建记录缺少 engine 字段"
    if engine.lower() not in allowed_engines:
        return False, f"LaTeX 引擎不在允许列表: {engine}（允许: {', '.join(allowed_engines)}）"

    # 检查 PDF 路径是否与实际交付路径一致
    recorded_pdf_path = build_data.get("pdf_path", "")
    if not recorded_pdf_path:
        return False, "构建记录缺少 pdf_path 字段"
    if recorded_pdf_path != pdf_path:
        return (
            False,
            f"构建记录中的 PDF 路径 ({recorded_pdf_path}) 与实际交付路径 ({pdf_path}) 不一致",
        )

    # 检查构建日志是否存在
    log_path = build_data.get("log_path")
    if not log_path:
        return False, "构建记录缺少 log_path 字段"
    log_file, log_err = _safe_resolve_path(root, log_path)
    if log_err:
        return False, f"构建日志路径无效: {log_path} ({log_err})"
    if not log_file or not log_file.exists():
        return False, f"构建日志不存在: {log_path}"

    # 检查 PDF 哈希
    recorded_hash = build_data.get("pdf_sha256")
    if not recorded_hash:
        return False, "构建记录中缺少 pdf_sha256"

    actual_hash = _sha256_file(pdf_file)
    if actual_hash != recorded_hash:
        return False, f"PDF 哈希不匹配：记录={recorded_hash}，实际={actual_hash}"

    # 检查源码哈希（必须包含 main_tex）
    source_hashes = build_data.get("source_hashes", {})
    if not source_hashes:
        return False, "构建记录缺少 source_hashes（至少应包含 main.tex）"

    # 验证源码哈希与当前文件一致
    main_tex_found = False
    for rel_path, recorded_src_hash in source_hashes.items():
        src_file, src_err = _safe_resolve_path(root, rel_path)
        if src_err:
            return False, f"构建记录中的源码路径无效: {rel_path} ({src_err})"

        if not src_file or not src_file.exists():
            return False, f"构建时源码已消失: {rel_path}"

        actual_src_hash = _sha256_file(src_file)
        if actual_src_hash != recorded_src_hash:
            return False, f"源码 {rel_path} 在编译后发生变化，构建记录已失效"

        if "main.tex" in rel_path:
            main_tex_found = True

    if not main_tex_found:
        return False, "构建记录 source_hashes 必须包含 main.tex"

    # 检查 PDF 来源记录为当前 LaTeX 项目
    recorded_main_tex = build_data.get("main_tex", "")
    if not recorded_main_tex:
        return False, "构建记录缺少 main_tex 字段"

    # 验证 main_tex 对应当前 paper/latex/main.tex
    expected_main_tex = "paper/latex/main.tex"
    if recorded_main_tex != expected_main_tex:
        return (
            False,
            f"构建记录的 main_tex ({recorded_main_tex}) 与当前 LaTeX 项目 ({expected_main_tex}) 不匹配",
        )

    return True, ""


def _check_build_evidence(root: Path, index: dict) -> tuple[bool, list[str]]:
    """检查构建证据文件是否完整。"""
    issues = []
    paper_deliverables = index.get("paper_deliverables", {})

    # 检查 DOCX 构建记录
    docx_record = paper_deliverables.get("docx", {}).get("build_record")
    if docx_record:
        record_path, path_err = _safe_resolve_path(root, docx_record)
        if path_err:
            issues.append(f"DOCX 构建记录路径无效: {docx_record} ({path_err})")
        elif record_path and record_path.exists():
            try:
                record_data = json.loads(record_path.read_text(encoding="utf-8"))
                required_fields = [
                    "status",
                    "tool",
                    "command",
                    "return_code",
                    "docx_path",
                    "started_at",
                    "finished_at",
                ]
                missing_fields = [f for f in required_fields if f not in record_data]
                if missing_fields:
                    issues.append(f"DOCX 构建记录缺少字段: {missing_fields}")
                if record_data.get("status") != "succeeded":
                    issues.append(f"DOCX 构建状态非 succeeded: {record_data.get('status')}")
                if record_data.get("return_code") != 0:
                    issues.append(f"DOCX 构建退出码非零: {record_data.get('return_code')}")
                if not record_data.get("tool"):
                    issues.append("DOCX 构建记录缺少 tool 字段")
                if not record_data.get("command"):
                    issues.append("DOCX 构建记录缺少 command 字段")
                if not record_data.get("started_at") or not record_data.get("finished_at"):
                    issues.append("DOCX 构建记录缺少时间戳（started_at/finished_at）")
            except (json.JSONDecodeError, Exception) as e:
                issues.append(f"DOCX 构建记录解析失败: {e}")
        else:
            issues.append(f"DOCX 构建记录不存在: {docx_record}")

    # 检查 LaTeX 构建记录
    latex_record = paper_deliverables.get("latex", {}).get("build_record")
    if latex_record:
        record_path, path_err = _safe_resolve_path(root, latex_record)
        if path_err:
            issues.append(f"LaTeX 构建记录路径无效: {latex_record} ({path_err})")
        elif record_path and record_path.exists():
            try:
                record_data = json.loads(record_path.read_text(encoding="utf-8"))
                required_fields = [
                    "status",
                    "engine",
                    "command",
                    "return_code",
                    "main_tex",
                    "source_hashes",
                    "pdf_path",
                    "pdf_sha256",
                    "log_path",
                    "started_at",
                    "finished_at",
                ]
                missing_fields = [f for f in required_fields if f not in record_data]
                if missing_fields:
                    issues.append(f"LaTeX 构建记录缺少字段: {missing_fields}")
                if record_data.get("status") != "succeeded":
                    issues.append(f"LaTeX 构建状态非 succeeded: {record_data.get('status')}")
                if record_data.get("return_code") != 0:
                    issues.append(f"LaTeX 编译退出码非零: {record_data.get('return_code')}")
                if not record_data.get("engine"):
                    issues.append("LaTeX 构建记录缺少 engine 字段")
                if not record_data.get("command"):
                    issues.append("LaTeX 构建记录缺少 command 字段")
                # source_hashes 必须非空且包含 main_tex
                source_hashes = record_data.get("source_hashes", {})
                if not source_hashes:
                    issues.append("LaTeX 构建记录 source_hashes 为空（至少应包含 main.tex）")
                elif not any("main.tex" in k for k in source_hashes.keys()):
                    issues.append("LaTeX 构建记录 source_hashes 必须包含 main.tex")

                # 检查时间戳
                if not record_data.get("started_at") or not record_data.get("finished_at"):
                    issues.append("LaTeX 构建记录缺少时间戳（started_at/finished_at）")

                # 检查日志路径
                log_path = record_data.get("log_path")
                if log_path:
                    log_file, log_err = _safe_resolve_path(root, log_path)
                    if log_err:
                        issues.append(f"LaTeX 构建日志路径无效: {log_path} ({log_err})")
            except (json.JSONDecodeError, Exception) as e:
                issues.append(f"LaTeX 构建记录解析失败: {e}")
        else:
            issues.append(f"LaTeX 构建记录不存在: {latex_record}")

    # 检查 LaTeX 编译日志
    latex_log_path, log_err = _safe_resolve_path(root, "paper/build/latex-compile.log")
    if log_err:
        issues.append(f"LaTeX 编译日志路径无效: paper/build/latex-compile.log ({log_err})")
    elif latex_log_path and latex_log_path.exists():
        # 检查日志文件大小和内容
        log_size = latex_log_path.stat().st_size
        if log_size == 0:
            issues.append("LaTeX 编译日志为空")
        elif log_size < 10:
            issues.append(f"LaTeX 编译日志过小（{log_size} 字节）")

        # 检查是否包含致命错误
        try:
            log_content = latex_log_path.read_text(encoding="utf-8", errors="ignore")
            # LaTeX 致命错误标记
            fatal_patterns = [
                "! LaTeX Error:",
                "! Emergency stop",
                "Fatal error",
                "! Undefined control sequence",
            ]
            if any(pattern in log_content for pattern in fatal_patterns):
                issues.append("LaTeX 编译日志包含致命错误")
        except Exception:
            pass  # 日志读取失败不影响主要检查
    else:
        issues.append("LaTeX 编译日志不存在: paper/build/latex-compile.log")

    # 检查内容清单
    manifest_path, manifest_err = _safe_resolve_path(root, "paper/content-manifest.json")
    if manifest_err:
        issues.append(f"内容清单路径无效: paper/content-manifest.json ({manifest_err})")
    elif manifest_path and manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            # content-manifest.json 必须包含顶层字段
            if not isinstance(manifest, dict):
                issues.append("内容清单必须是 JSON 对象")
            else:
                # 检查必需字段（允许额外字段）
                required_categories = ["figures", "citations", "claims"]
                for cat in required_categories:
                    if cat not in manifest:
                        issues.append(f"内容清单缺少 {cat} 索引")
                    elif not isinstance(manifest[cat], list):
                        issues.append(f"内容清单的 {cat} 必须是数组")
        except (json.JSONDecodeError, Exception) as e:
            issues.append(f"内容清单 JSON 解析失败: {e}")
    else:
        issues.append("内容清单不存在: paper/content-manifest.json")

    return len(issues) == 0, issues


def _check_phase_paper_build(root: Path, index: dict) -> dict:
    """阶段 10：多格式构建与发布。"""
    result = {
        "phase": "paper_build",
        "passed": False,
        "missing": [],
        "invalid": [],
        "warnings": [],
        "next_action": "",
        "requires_user": False,
    }
    missing, invalid, warnings = result["missing"], result["invalid"], result["warnings"]

    paper_deliverables = index.get("paper_deliverables", {})
    if not paper_deliverables:
        invalid.append("modeling/index.json 缺少 paper_deliverables 字段")
        result["passed"] = False
        result["next_action"] = "初始化 paper_deliverables 字段"
        return result

    # 1. 检查四种格式状态必须全部为 completed
    for fmt in ["markdown", "docx", "latex", "pdf"]:
        fmt_info = paper_deliverables.get(fmt, {})
        fmt_status = fmt_info.get("status")
        if fmt_status != "completed":
            invalid.append(f"{fmt} 格式未完成（状态={fmt_status}）")

    # 2. 检查 Word（必须存在且为有效 OOXML）
    docx_info = paper_deliverables.get("docx", {})
    docx_path = docx_info.get("path", "paper/final.docx")
    if not docx_path:
        missing.append("paper_deliverables.docx.path 未设置")
    else:
        _check_file_exists(root, docx_path, missing, warnings)
        if docx_path not in missing:  # 文件存在时才检查格式
            valid, err = _check_docx_valid(root, docx_path)
            if not valid:
                invalid.append(f"Word 文档无效: {err}")

    # 3. 检查 LaTeX（必须存在且引用完整）
    latex_info = paper_deliverables.get("latex", {})
    latex_project = latex_info.get("project_path", "paper/latex")
    main_tex = latex_info.get("main_tex", "paper/latex/main.tex")
    if not main_tex:
        missing.append("paper_deliverables.latex.main_tex 未设置")
    else:
        _check_file_exists(root, main_tex, missing, invalid)
        if main_tex not in missing:
            latex_issues = _check_latex_references(root, latex_project)
            invalid.extend(latex_issues)

    # 4. 检查 PDF（必须存在且可追溯）
    pdf_info = paper_deliverables.get("pdf", {})
    pdf_path = pdf_info.get("path", "paper/final.pdf")
    if not pdf_path:
        missing.append("paper_deliverables.pdf.path 未设置")
    else:
        build_record = pdf_info.get("build_record")
        if not build_record:
            invalid.append("PDF 缺少 build_record 引用")
        else:
            valid, err = _check_pdf_source(root, pdf_path, build_record)
            if not valid:
                invalid.append(f"PDF 来源无效: {err}")

    # 5. 检查构建证据
    evidence_ok, evidence_issues = _check_build_evidence(root, index)
    if not evidence_ok:
        invalid.extend(evidence_issues)

    result["passed"] = len(missing) == 0 and len(invalid) == 0
    if not result["passed"]:
        result["next_action"] = "修复论文交付物或构建证据"
    return result


def _check_phase_final_audit(root: Path, index: dict, record: bool = False) -> dict:
    """阶段 10：一致性检查与完成审计。

    Args:
        root: 项目根目录
        index: 状态索引
        record: 是否返回记录信息（实际写入由 validate_project 统一处理）
    """
    result = {
        "phase": "final_audit",
        "passed": False,
        "missing": [],
        "invalid": [],
        "warnings": [],
        "next_action": "",
        "requires_user": False,
        "evidence": [],
        "missing_items": [],
    }
    missing, invalid, warnings = result["missing"], result["invalid"], result["warnings"]

    # 1. 检查必需文件
    required_files = [
        "statement/problem.md",
        "statement/requirements.md",
        "statement/constraints.md",
        "analysis/problem_analysis.md",
        "analysis/data_profile.md",
        "research/references.json",
        "model/assumptions.md",
        "model/notation.md",
        "model/selection.md",
        "paper/outline.md",
        "paper/final.md",
        "paper/references.md",
    ]
    for rel in required_files:
        _check_file_exists(root, rel, missing, warnings)
        if _check_placeholder(root, rel, invalid):
            invalid.append(f"{rel} 仍为占位内容")

    # 2. 检查子问题完成状态
    subproblems = index.get("subproblems", [])
    if not subproblems:
        invalid.append("subproblems 为空，至少需要一个子问题")
    else:
        incomplete = [sp for sp in subproblems if sp.get("status") != "completed"]
        if incomplete:
            invalid.append(f"子问题未完成: {[sp.get('id') for sp in incomplete]}")

    # 3. 检查模型和运行（必须有至少一个模型和成功运行）
    selected_models = index.get("selected_models", [])
    runs = index.get("runs", [])
    validations = index.get("validations", [])

    if not selected_models:
        invalid.append("selected_models 为空，至少需要一个选定模型")
    else:
        # 每个主模型必须有成功运行
        for model in selected_models:
            model_id = model.get("model_id")
            has_success_run = any(
                r.get("model_id") == model_id and r.get("status") == "succeeded" for r in runs
            )
            if not has_success_run:
                invalid.append(f"模型 {model_id} 无成功运行")

            # 每个主模型必须有通过检验（检查 validations 中的摘要）
            has_passed_val = any(
                v.get("primary_model_ids", [])
                and model_id in v.get("primary_model_ids", [])
                and v.get("passed")
                for v in validations
            )
            if not has_passed_val:
                invalid.append(f"模型 {model_id} 无通过的检验")

    if not runs:
        invalid.append("runs 为空，至少需要一个成功运行")

    # 4. 检查运行证据
    for run in runs:
        if run.get("status") != "succeeded":
            continue
        if not run.get("log_paths"):
            invalid.append(f"运行 {run.get('run_id')} 无日志")
        if not run.get("result_paths"):
            invalid.append(f"运行 {run.get('run_id')} 无结果")

    # 5. 检查验证结果
    # 5.1 检查 validation/plan.json
    plan, plan_err = _load_json_object(root, "validation/plan.json")
    if plan_err:
        invalid.append(f"验证计划不可用: {plan_err}")

    # 5.2 检查 validation/validation.json
    validation_json, val_err = _load_json_object(root, "validation/validation.json")
    if val_err:
        invalid.append(f"验证结果不可用: {val_err}")
    else:
        # 检查协议一致性
        if plan:
            protocol_hash = plan.get("protocol_hash", "")
            split_id = plan.get("dataset_split_id", "")

            # 检查主模型和基线的运行是否采用相同协议
            primary_ids = plan.get("primary_model_ids", [])
            baseline_ids = plan.get("baseline_model_ids", [])
            comparable_issues = _check_comparable_runs(
                root, primary_ids, baseline_ids, protocol_hash, split_id
            )
            invalid.extend(comparable_issues)

            # 检查验证计划中的条件是否都有实测值
            criteria_results = validation_json.get("criteria_results", [])
            criteria_without_value = [c for c in criteria_results if c.get("observed") is None]
            if criteria_without_value:
                invalid.append(
                    f"以下验证条件缺少实测值: {[c.get('criterion_id') for c in criteria_without_value]}"
                )

            # 检查整体验证状态是否由真实条件计算
            computed_passed = _compute_validation_passed(validation_json)
            if not computed_passed:
                invalid.append("验证结果未通过（根据实际指标计算）")

        # 检查 comparison.md
        _check_file_exists(root, "validation/comparison.md", missing, warnings)

    # 6. 检查论文交付物专项
    paper_deliverables = index.get("paper_deliverables", {})
    if not paper_deliverables:
        invalid.append("modeling/index.json 缺少 paper_deliverables 字段")
    else:
        # 6.1 检查四种格式状态必须全部为 completed
        for fmt in ["markdown", "docx", "latex", "pdf"]:
            fmt_info = paper_deliverables.get(fmt, {})
            fmt_status = fmt_info.get("status")
            if fmt_status != "completed":
                invalid.append(f"{fmt} 格式未完成（状态={fmt_status}）")

        # 6.2 检查 Word（必须存在且为有效 OOXML）
        docx_info = paper_deliverables.get("docx", {})
        docx_path = docx_info.get("path", "paper/final.docx")
        _check_file_exists(root, docx_path, missing, warnings)
        if docx_path not in missing:  # 文件存在时才检查格式
            valid, err = _check_docx_valid(root, docx_path)
            if not valid:
                invalid.append(f"Word 文档无效: {err}")

        # 6.3 检查 LaTeX（必须存在且引用完整）
        latex_info = paper_deliverables.get("latex", {})
        latex_project = latex_info.get("project_path", "paper/latex")
        main_tex = latex_info.get("main_tex", "paper/latex/main.tex")
        _check_file_exists(root, main_tex, missing, invalid)
        if main_tex not in missing:
            latex_issues = _check_latex_references(root, latex_project)
            invalid.extend(latex_issues)

        # 6.4 检查 PDF（必须存在且可追溯）
        pdf_info = paper_deliverables.get("pdf", {})
        pdf_path = pdf_info.get("path", "paper/final.pdf")
        build_record = pdf_info.get("build_record")
        if not build_record:
            invalid.append("PDF 缺少 build_record 引用")
        else:
            valid, err = _check_pdf_source(root, pdf_path, build_record)
            if not valid:
                invalid.append(f"PDF 来源无效: {err}")

        # 6.5 检查构建证据
        evidence_ok, evidence_issues = _check_build_evidence(root, index)
        if not evidence_ok:
            invalid.extend(evidence_issues)

    # 7. 检查图片引用
    final_md = root / "paper" / "final.md"
    if final_md.exists():
        content = final_md.read_text(encoding="utf-8")
        for line in content.splitlines():
            if "![" in line and "](" in line:
                try:
                    start = line.index("](") + 2
                    end = line.index(")", start)
                    img_path = line[start:end]
                    if not img_path.startswith("http"):
                        img_full, err = _safe_resolve_path(root, img_path)
                        if err:
                            invalid.append(f"图片路径无效: {img_path} ({err})")
                        elif not img_full or not img_full.exists():
                            invalid.append(f"图片不存在: {img_path}")
                except (ValueError, IndexError):
                    warnings.append(f"无法解析图片链接: {line[:50]}")

    result["passed"] = len(missing) == 0 and len(invalid) == 0
    result["audit_written"] = False  # 写入由 validate_project 统一处理
    return result


def _write_json(path: Path, data: dict) -> None:
    """原子写入 JSON 文件。"""
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def _write_audit(root: Path, audit: dict) -> None:
    """原子写入审计结果。"""
    index_path = root / "modeling" / "index.json"
    try:
        existing = json.loads(index_path.read_text(encoding="utf-8"))
        existing["completion_audit"] = audit
        existing["last_updated"] = _utc_now()
        _write_json(index_path, existing)
    except Exception as e:
        # 记录错误但不抛出异常
        print(f"警告: 写入审计结果失败: {e}", file=sys.stderr)


def _write_audit_failed(root: Path, index: dict, result: dict) -> None:
    """写入失败的审计结果，确保清除旧的 passed=true，并生成审计报告文件。"""
    index_path = root / "modeling" / "index.json"
    try:
        # 加载最新的 index
        if index_path.exists():
            existing = json.loads(index_path.read_text(encoding="utf-8"))
        else:
            existing = index

        # 收集缺失和无效项
        missing_items = result.get("missing", [])
        invalid_items = result.get("invalid", [])

        # 强制设置失败状态
        existing["completion_audit"] = {
            "passed": False,
            "checked_at": _utc_now(),
            "evidence": result.get("phase_results", {}).get("final_audit", {}).get("evidence", []),
            "missing_items": missing_items + invalid_items,
        }
        existing["status"] = "active"  # 恢复为活动状态
        existing["last_updated"] = _utc_now()

        # 如果有最终审计阶段，确保其状态不是 passed
        if "final_audit" in existing.get("phase_gates", {}):
            existing["phase_gates"]["final_audit"]["status"] = "failed"
            existing["phase_gates"]["final_audit"]["checked_at"] = _utc_now()

        _write_json(index_path, existing)

        # 生成审计报告文件（失败时也必须生成）
        _write_completion_report(root, result)
    except Exception as e:
        print(f"警告: 写入失败审计结果时出错: {e}", file=sys.stderr)


def _write_completion_report(root: Path, validation_result: dict) -> None:
    """生成审计报告文件，missing 与 invalid 分开呈现。"""
    report_path = root / "audit" / "completion_report.md"

    # 生成报告内容
    phase_results = validation_result.get("phase_results", {})
    final_audit = phase_results.get("final_audit", {})

    lines = [
        "# 完整性审计报告",
        "",
        f"- **审计时间**：{_utc_now()}",
        f"- **项目状态**：{'通过' if validation_result['passed'] else '未通过'}",
        "",
        "## 审核结果",
        "",
        f"**总体结论**：{'项目完整且可以标记为完成' if validation_result['passed'] else '存在未解决的问题，需要修正后才能完成'}",
        "",
    ]

    # 已验证证据
    evidence = final_audit.get("evidence", [])
    lines.extend(["## 已验证证据", ""])
    if evidence:
        for ev in evidence:
            lines.append(f"- {ev}")
    else:
        lines.append("- 无")
    lines.append("")

    # 缺失项（missing）
    missing_items = validation_result.get("missing", [])
    lines.extend(["## 缺失项", ""])
    if missing_items:
        for item in missing_items:
            lines.append(f"- {item}")
    else:
        lines.append("- 无缺失")
    lines.append("")

    # 无效项（invalid）
    invalid_items = validation_result.get("invalid", [])
    lines.extend(["## 无效项", ""])
    if invalid_items:
        for item in invalid_items:
            lines.append(f"- {item}")
    else:
        lines.append("- 无无效")
    lines.append("")

    # 各阶段检查结果
    lines.extend(
        ["## 阶段检查详情", "", "| 阶段 | 状态 | 缺失 | 无效 |", "|------|------|------|------|"]
    )
    for phase_name, phase_data in phase_results.items():
        status = "通过" if phase_data.get("passed") else "失败"
        missing_count = len(phase_data.get("missing", []))
        invalid_count = len(phase_data.get("invalid", []))
        lines.append(f"| {phase_name} | {status} | {missing_count} | {invalid_count} |")

    lines.append("")

    # 警告
    warnings = validation_result.get("warnings", [])
    if warnings:
        lines.extend(["## 警告", ""])
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    # 审计结论
    lines.extend(["## 审计结论", ""])
    if validation_result["passed"]:
        lines.append("- 所有检查通过，项目可以标记为完成")
    else:
        lines.append("- 存在未解决的问题，需要修正后才能完成")

    # 写入文件
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


# 阶段处理器
_PHASE_HANDLERS = {
    "intake": _check_phase_intake,
    "problem_analysis": _check_phase_problem_analysis,
    "literature_research": _check_phase_literature_research,
    "model_design": _check_phase_model_design,
    "model_establishment": _check_phase_model_establishment,
    "model_solving": _check_phase_model_solving,
    "model_validation": _check_phase_model_validation,
    "result_interpretation": _check_phase_result_interpretation,
    "paper_writing": _check_phase_paper_writing,
    "paper_build": _check_phase_paper_build,
    "final_audit": _check_phase_final_audit,
}


def _check_gate_invalidation(
    root: Path, index: dict, record: bool = False
) -> tuple[list[str], list[str]]:
    """检查门禁是否因输入变化而失效。

    Args:
        root: 项目根目录
        index: 状态索引
        record: 是否写入失效时间戳

    Returns:
        (warnings, failures) 元组，failures 是导致失败的失效项
    """
    warnings: list[str] = []
    failures: list[str] = []
    runs = index.get("runs", [])
    changed = False

    for run in runs:
        if run.get("status") != "succeeded":
            continue
        input_hashes = run.get("input_hashes", {})
        if not input_hashes:
            continue
        for rel_path, recorded_hash in input_hashes.items():
            # 使用安全路径解析
            target, err = _safe_resolve_path(root, rel_path)
            if err:
                msg = f"运行 {run.get('run_id')} 的输入路径无效: {rel_path} ({err})"
                warnings.append(msg)
                failures.append(msg)
                changed = True
                if record:
                    run["invalidated_at"] = _utc_now()
                    run["invalidated_reason"] = f"输入路径无效: {rel_path}"
                continue

            if not target or not target.exists():
                msg = f"运行 {run.get('run_id')} 的输入文件消失: {rel_path}"
                warnings.append(msg)
                failures.append(msg)
                changed = True
                if record:
                    run["invalidated_at"] = _utc_now()
                    run["invalidated_reason"] = f"输入文件消失: {rel_path}"
            else:
                # 文件存在，检查哈希
                import hashlib

                h = hashlib.sha256()
                try:
                    h.update(target.read_bytes())
                    actual_hash = f"sha256:{h.hexdigest()}"
                    if actual_hash != recorded_hash:
                        msg = f"运行 {run.get('run_id')} 的输入文件已修改: {rel_path}"
                        warnings.append(msg)
                        failures.append(msg)
                        changed = True
                        if record and not run.get("invalidated_at"):
                            run["invalidated_at"] = _utc_now()
                            run["invalidated_reason"] = f"输入文件已修改: {rel_path}"
                except Exception:
                    msg = f"运行 {run.get('run_id')} 的输入文件无法读取: {rel_path}"
                    warnings.append(msg)
                    failures.append(msg)
                    changed = True

    if record and changed:
        # 原子写入更新后的 index
        index_path = root / "modeling" / "index.json"
        _write_json(index_path, index)

    return warnings, failures


def _update_phase_gate(
    root: Path,
    index: dict,
    phase: str,
    passed: bool,
    persist: bool = False,
    evidence: list[str] | None = None,
) -> None:
    """更新阶段门禁状态。

    Args:
        root: 项目根目录
        index: 状态索引（会被修改）
        phase: 阶段名称
        passed: 是否通过
        persist: 是否立即原子写回 index.json
        evidence: 证据路径列表（可选）
    """
    phase_gates = index.get("phase_gates", {})
    gate = phase_gates.get(phase, {})
    gate["status"] = "passed" if passed else "failed"
    gate["checked_at"] = _utc_now()
    if evidence:
        gate["evidence_paths"] = evidence
    phase_gates[phase] = gate
    index["phase_gates"] = phase_gates
    # 不修改 current_phase，由调用方在适当位置设置
    index["last_updated"] = _utc_now()

    if persist:
        _write_json(root / "modeling" / "index.json", index)


def _phase_evidence_and_hashes(root: Path, phase: str, index: dict) -> tuple[list[str], dict]:
    """收集阶段证据路径和输入哈希。

    Args:
        root: 项目根目录
        phase: 阶段名称
        index: 状态索引

    Returns:
        (evidence_paths, input_hashes) 元组
    """
    evidence_paths = []
    input_hashes = {}

    # 根据阶段收集证据路径
    if phase == "intake":
        evidence_paths = [
            "statement/problem.md",
            "statement/requirements.md",
            "statement/constraints.md",
        ]
    elif phase == "problem_analysis":
        evidence_paths = [
            "analysis/problem_analysis.md",
            "analysis/data_profile.md",
        ]
        # 收集数据文件哈希
        data_dir = root / "data" / "processed"
        if data_dir.exists():
            for data_file in data_dir.glob("*.csv"):
                rel_path = str(data_file.relative_to(root))
                file_hash = _sha256_file(data_file)
                if file_hash:
                    input_hashes[rel_path] = file_hash
    elif phase == "literature_research":
        evidence_paths = [
            "research/references.json",
            "paper/references.md",
        ]
    elif phase == "model_design":
        evidence_paths = [
            "model/assumptions.md",
            "model/notation.md",
            "model/selection.md",
        ]
    elif phase == "model_establishment":
        evidence_paths = []
        # 从 selected_models 收集 formulation 和 algorithm 路径
        selected_models = index.get("selected_models", [])
        for model in selected_models:
            model_id = model.get("model_id", "")
            fmt_path = model.get("formulation_path", f"model/{model_id}/formulation.md")
            alg_path = model.get("algorithm_path", f"model/{model_id}/algorithm.md")
            evidence_paths.append(fmt_path)
            evidence_paths.append(alg_path)
        evidence_paths.append("validation/plan.json")
    elif phase == "model_solving":
        evidence_paths = []
        # 从 runs 收集日志和结果路径
        runs = index.get("runs", [])
        for run in runs:
            log_paths = run.get("log_paths", [])
            result_paths = run.get("result_paths", [])
            evidence_paths.extend(log_paths)
            evidence_paths.extend(result_paths)
            # 收集输入哈希
            run_input_hashes = run.get("input_hashes", {})
            input_hashes.update(run_input_hashes)
    elif phase == "model_validation":
        evidence_paths = [
            "validation/validation.json",
            "validation/validation.md",
            "validation/comparison.md",
            "validation/sensitivity.md",
        ]
    elif phase == "result_interpretation":
        evidence_paths = [
            "results/summary.md",
            "results/figures/",
            "results/tables/",
        ]
    elif phase == "paper_writing":
        evidence_paths = [
            "paper/outline.md",
            "paper/final.md",
            "paper/references.md",
        ]
    elif phase == "paper_build":
        evidence_paths = [
            "paper/final.docx",
            "paper/latex/main.tex",
            "paper/final.pdf",
            "paper/build/docx-build.json",
            "paper/build/latex-build.json",
            "paper/build/latex-compile.log",
            "paper/content-manifest.json",
        ]
    elif phase == "final_audit":
        evidence_paths = [
            "audit/completion_report.md",
        ]

    # 过滤掉空路径
    evidence_paths = [p for p in evidence_paths if p]

    return evidence_paths, input_hashes


def _record_single_phase(root: Path, index: dict, phase: str, phase_result: dict) -> None:
    """单阶段 --record 独立落盘，不依赖 final_audit。"""
    if phase == "final_audit":
        # final_audit 由主流程处理
        return

    # 收集证据路径和输入哈希
    evidence, input_hashes = _phase_evidence_and_hashes(root, phase, index)

    # 更新阶段门禁状态并立即落盘
    _update_phase_gate(
        root,
        index,
        phase,
        phase_result["passed"],
        persist=True,
        evidence=evidence,
    )

    # 如果有输入哈希，更新到 phase_gates
    if input_hashes:
        phase_gates = index.get("phase_gates", {})
        gate = phase_gates.get(phase, {})
        gate["input_hashes"] = input_hashes
        phase_gates[phase] = gate
        index["phase_gates"] = phase_gates
        _write_json(root / "modeling" / "index.json", index)


def validate_project(
    project_root: str | Path,
    *,
    phase: str = "current",
    json_output: bool = False,
    record: bool = False,
) -> dict:
    """主入口。

    Args:
        project_root: 项目根目录
        phase: 要检查的阶段（current / <阶段名> / all）
        json_output: 是否输出 JSON
        record: 是否写入审计结果和失效记录

    Returns:
        包含验证结果的字典，包括 passed、missing、invalid、warnings 等字段
    """
    root = _resolve_project_root(project_root)

    result: dict = {
        "project_root": str(root),
        "phase": phase,
        "passed": False,
        "missing": [],
        "invalid": [],
        "warnings": [],
        "next_action": "",
        "requires_user": False,
        "error": None,
        "phase_results": {},
        "audit_written": False,
    }

    try:
        index, load_err = _load_index(root)
        if load_err:
            result["error"] = load_err
            result["invalid"].append(load_err)
            # 不提前返回，让后面的退出码逻辑处理
        else:
            # 确定要检查的阶段
            phases_to_check = []
            if phase == "current":
                current = index.get("current_phase", "intake")
                phases_to_check = [current]
            elif phase == "all":
                phases_to_check = _PHASE_ORDER.copy()
            elif phase in _PHASE_HANDLERS:
                phases_to_check = [phase]
            else:
                # 未知 phase
                result["error"] = f"未知阶段: {phase}"
                result["invalid"].append(f"未知阶段: {phase}")

            if not result["error"]:
                # 执行校验
                all_passed = True
                first_failure_action = None
                first_failure_requires_user = False

                for p in phases_to_check:
                    handler = _PHASE_HANDLERS.get(p)
                    if not handler:
                        result["error"] = f"未实现阶段处理器: {p}"
                        result["phase_results"][p] = {"passed": False, "error": result["error"]}
                        all_passed = False
                        continue

                    if p == "final_audit":
                        phase_result = handler(root, index, record=record)
                    else:
                        phase_result = handler(root, index)

                    # 如果 --record 且不是 final_audit，立即独立落盘
                    if record and p != "final_audit":
                        _record_single_phase(root, index, p, phase_result)

                    result["phase_results"][p] = {
                        "passed": phase_result["passed"],
                        "missing": phase_result.get("missing", []),
                        "invalid": phase_result.get("invalid", []),
                        "warnings": phase_result.get("warnings", []),
                    }
                    result["missing"].extend(phase_result.get("missing", []))
                    result["invalid"].extend(phase_result.get("invalid", []))
                    result["warnings"].extend(phase_result.get("warnings", []))

                    if not phase_result["passed"]:
                        all_passed = False
                        # 记录第一个失败的阶段，但不停止检查其他阶段
                        if first_failure_action is None:
                            first_failure_action = phase_result.get("next_action", "")
                            first_failure_requires_user = phase_result.get("requires_user", False)

                # 门禁失效检查（仅在成功加载 index 后执行）
                gate_warnings, gate_failures = _check_gate_invalidation(root, index, record=record)
                result["warnings"].extend(gate_warnings)
                if gate_failures:
                    # 输入失效导致失败
                    result["invalid"].extend(gate_failures)
                    all_passed = False
                    if first_failure_action is None:
                        first_failure_action = "输入文件已变化，相关门禁失效，请重新运行受影响模型"

                # 最终结果计算：只有所有检查通过才算通过
                result["passed"] = (
                    all_passed and len(result["missing"]) == 0 and len(result["invalid"]) == 0
                )

                # next_action 指向第一个失败阶段
                if first_failure_action:
                    result["next_action"] = first_failure_action
                    result["requires_user"] = first_failure_requires_user

                # 统一处理审计结果写入
                if record:
                    if all_passed and "final_audit" in phases_to_check:
                        final_audit_result = result["phase_results"].get("final_audit", {})
                        if final_audit_result.get("passed"):
                            # 全部通过：一次性、原子地写入所有状态
                            audit = {
                                "passed": True,
                                "checked_at": _utc_now(),
                                "evidence": final_audit_result.get("evidence", []),
                                "missing_items": [],
                            }
                            _write_audit(root, audit)

                            # 更新所有已通过阶段的门禁状态（原子写回）
                            for p in phases_to_check:
                                if p != "final_audit":
                                    phase_gates = index.get("phase_gates", {})
                                    gate = phase_gates.get(p, {})
                                    gate["status"] = "passed"
                                    gate["checked_at"] = _utc_now()
                                    gate["evidence_paths"] = (
                                        result["phase_results"].get(p, {}).get("evidence", [])
                                    )
                                    phase_gates[p] = gate
                                    index["phase_gates"] = phase_gates

                            # 更新项目状态和当前阶段
                            index["current_phase"] = "final_audit"
                            index["status"] = "completed"
                            index["last_updated"] = _utc_now()

                            # 一次性原子写回 index
                            _write_json(root / "modeling" / "index.json", index)

                            # 生成审计报告文件
                            _write_completion_report(root, result)
                            result["audit_written"] = True
                        else:
                            # final_audit 本身失败
                            _write_audit_failed(root, index, result)
                            result["audit_written"] = True
                    else:
                        # 有任何失败：写入失败状态，确保清除旧的 passed=true
                        _write_audit_failed(root, index, result)
                        result["audit_written"] = True

    except Exception as exc:
        result["error"] = str(exc)
        result["invalid"].append(str(exc))

    return result


def main():
    parser = argparse.ArgumentParser(description="校验数学建模项目")
    parser.add_argument("--project-root", default=None, help="工作区根目录")
    parser.add_argument(
        "--phase",
        default="current",
        help="要检查的阶段（current / <阶段名> / all）",
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--record", action="store_true", help="写入审计结果和失效记录")
    parser.add_argument("--all", action="store_true", help="检查所有阶段")
    args = parser.parse_args()

    # 处理 --all 标志
    if args.all:
        phase = "all"
    else:
        phase = args.phase

    # 调用验证函数
    result = validate_project(
        args.project_root, phase=phase, json_output=args.json, record=args.record
    )

    # 输出 JSON 结果
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    # 根据结果返回退出码（validate_project 不直接 exit，由 main 统一处理）
    if result.get("error"):
        sys.exit(2)
    elif not result.get("passed"):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
