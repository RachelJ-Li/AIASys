# modeling/index.json 字段定义

## 目录

1. [项目路径规范](#项目路径规范)
2. [顶层结构](#顶层结构)
3. [字段定义](#字段定义)
4. [phase_gates 结构](#phase_gates-结构)
5. [paper_deliverables 结构](#paper_deliverables-结构)
6. [completion_audit 结构](#completion_audit-结构)

## 项目路径规范

```
statement/                    # 赛题与要求
data/raw/                     # 原始数据
data/processed/               # 处理后数据
analysis/                     # 问题分析
research/notes/               # 文献笔记
model/                        # 模型定义
model/<model_id>/             # 具体模型
src/<model_id>/               # 求解代码
configs/                      # 配置
runs/<run_id>/                # 运行记录
validation/                   # 模型检验
validation/validation.md      # 检验报告
validation/sensitivity.md     # 敏感性分析
results/summary.md            # 结果汇总
results/figures/              # 最终图表
results/tables/               # 最终表格
paper/outline.md              # 论文大纲
paper/final.md                # Markdown 主稿
paper/references.md           # 参考文献
paper/final.docx              # Word 论文
paper/latex/                  # LaTeX 源码项目
  main.tex                    # LaTeX 主文件
paper/final.pdf               # 编译后的 PDF
paper/build/                   # 构建证据
  docx-build.json
  latex-build.json
  latex-compile.log
paper/content-manifest.json   # 跨格式内容索引
audit/completion_report.md    # 审计报告
modeling/index.json           # 项目状态索引
```

## 顶层结构

```json
{
  "schema_version": 1,
  "project": {},
  "research_policy": {},
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
  "paper_deliverables": {},
  "blockers": [],
  "next_actions": [],
  "phase_gates": {},
  "completion_audit": {},
  "last_updated": null
}
```

## 字段定义

### schema_version

- **类型**：整数
- **说明**：schema 版本号，当前为 2

### project

```json
{
  "name": "",
  "type": "",
  "problem_type": [],
  "deadline": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 项目名称 |
| type | string | 竞赛类型（如 "math-modeling"）|
| problem_type | string[] | 问题类型（如 ["optimization", "prediction"]）|
| deadline | string\|null | 截止时间（ISO 8601）|

### research_policy

```json
{
  "rules_checked": false,
  "network_allowed": true,
  "external_sources_allowed": true,
  "constraint_source": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| rules_checked | boolean | 是否已检查赛题联网规则 |
| network_allowed | boolean | 是否允许联网 |
| external_sources_allowed | boolean | 是否允许外部资料 |
| constraint_source | string\|null | 规则来源（如 "statement/constraints.md#L5"）|

### current_phase

- **类型**：字符串
- **枚举值**：
  - `intake`
  - `problem_analysis`
  - `literature_research`
  - `model_design`
  - `model_establishment`
  - `model_solving`
  - `model_validation`
  - `result_interpretation`
  - `paper_writing`
  - `final_audit`

### status

- **类型**：字符串
- **枚举值**：
  - `active`：进行中
  - `blocked`：等待用户
  - `failed`：本轮失败
  - `revision_required`：需返工
  - `completed`：已完成

### subproblems

```json
[
  {
    "id": "P1",
    "title": "",
    "requirement_refs": [],
    "input_paths": [],
    "expected_outputs": [],
    "dependencies": [],
    "status": "pending"
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 子问题 ID（如 "P1"）|
| title | string | 标题 |
| requirement_refs | string[] | 对应 requirements 中的位置 |
| input_paths | string[] | 输入文件路径 |
| expected_outputs | string[] | 期望输出 |
| dependencies | string[] | 依赖的子问题 ID |
| status | string | `pending` / `in_progress` / `completed` |

### assumptions

```json
[
  {
    "id": "H1",
    "content": "",
    "basis": "",
    "validation_method": ""
  }
]
```

### notations

```json
[
  {
    "symbol": "",
    "meaning": "",
    "unit": "",
    "type": "scalar|vector|matrix"
  }
]
```

### model_candidates

```json
[
  {
    "model_id": "C1",
    "name": "",
    "family": "",
    "applicability": "",
    "complexity": "",
    "interpretability": "",
    "status": "candidate"
  }
]
```

### selected_models

```json
[
  {
    "model_id": "M1",
    "subproblem_ids": ["P1"],
    "family": "",
    "role": "primary",
    "baseline_model_ids": ["B1"],
    "selection_reason": "",
    "formulation_path": "model/M1/formulation.md",
    "algorithm_path": "model/M1/algorithm.md",
    "config_path": "configs/M1.json",
    "validation_plan_path": "validation/plan.json",
    "status": "selected"
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| model_id | string | 模型 ID |
| subproblem_ids | string[] | 关联子问题 |
| family | string | 模型族（optimization、prediction、classification 等）|
| role | string | 角色：primary（主模型）或 baseline（基线）|
| baseline_model_ids | string[] | 基线模型 ID 列表（role=primary 时使用）|
| selection_reason | string | 选择理由 |
| formulation_path | string | 模型公式文件路径 |
| algorithm_path | string | 算法步骤文件路径 |
| config_path | string | 配置文件路径 |
| validation_plan_path | string | 验证计划文件路径（validation/plan.json）|
| status | string | 状态：selected |

基线模型（role=baseline）额外字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| baseline_for | string[] | 被哪个主模型用作基线（包含该主模型的 model_id）|

**基线豁免**：确实无法设置基线时登记：

```json
{
  "required": false,
  "reason": "不存在可运行的同类基线",
  "evidence_paths": ["model/selection.md"],
  "alternative": "解析解对比与消融实验"
}
```

### runs

```json
[
  {
    "run_id": "run-001",
    "model_id": "M1",
    "model_role": "primary|baseline",
    "command": "",
    "status": "succeeded|failed",
    "started_at": "",
    "finished_at": "",
    "random_seed": null,
    "runtime": {},
    "dependencies": {},
    "parameters": {},
    "reproduce_command": "",
    "input_hashes": {},
    "log_paths": [],
    "result_paths": [],
    "output_files": [],
    "run_scope": "minimum|full",
    "minimum_gate_passed": true,
    "protocol_path": "validation/plan.json",
    "protocol_hash": "sha256:...",
    "dataset_split_id": "split-001"
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| run_id | string | 运行 ID |
| model_id | string | 模型 ID |
| model_role | string | 角色：primary 或 baseline |
| command | string | 执行命令 |
| status | string | 状态：succeeded 或 failed |
| started_at | string | 开始时间（ISO 8601）|
| finished_at | string | 结束时间（ISO 8601）|
| random_seed | int\|null | 随机种子 |
| runtime | object | 运行环境信息 |
| dependencies | object | 依赖版本 |
| parameters | object | 运行参数 |
| reproduce_command | string | 复现命令 |
| input_hashes | object | 输入文件哈希 |
| log_paths | string[] | 日志文件路径 |
| result_paths | string[] | 结果文件路径 |
| output_files | string[] | 输出文件路径 |
| run_scope | string | 运行范围：minimum（最小验证）或 full（全量）|
| minimum_gate_passed | boolean | 最小运行门禁是否通过 |
| protocol_path | string | 验证协议路径（validation/plan.json）|
| protocol_hash | string | 验证协议哈希 |
| dataset_split_id | string | 数据集划分 ID |

**路径限制**：`log_paths`、`result_paths` 中的路径必须位于项目根目录内。

### validations

```json
[
  {
    "validation_id": "V1",
    "protocol_path": "validation/plan.json",
    "primary_model_ids": ["M1"],
    "baseline_model_ids": ["B1"],
    "run_ids": ["run-primary", "run-baseline"],
    "criteria_results": [],
    "criteria_passed": true,
    "comparison_passed": true,
    "stability_passed": true,
    "domain_checks_passed": true,
    "passed": true,
    "result_path": "validation/validation.json",
    "evidence_paths": [
      "validation/validation.md",
      "validation/comparison.md",
      "validation/sensitivity.md"
    ],
    "revision_action": null,
    "checked_at": ""
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| validation_id | string | 验证 ID（如 "V1"）|
| protocol_path | string | 验证计划路径（validation/plan.json）|
| primary_model_ids | string[] | 主模型 ID 列表 |
| baseline_model_ids | string[] | 基线模型 ID 列表 |
| run_ids | string[] | 关联运行 ID 列表 |
| criteria_results | array | 各条件实测值和通过状态（由校验器计算）|
| criteria_passed | boolean | 所有 required criteria 是否通过（由校验器计算）|
| comparison_passed | boolean | 基线对比是否通过（由校验器计算）|
| stability_passed | boolean | 稳定性验证是否通过（由校验器计算）|
| domain_checks_passed | boolean | 领域验证是否通过（由校验器计算）|
| passed | boolean | 整体通过状态（由校验器计算）|
| result_path | string | 验证结果文件路径（validation/validation.json）|
| evidence_paths | string[] | 证据文件路径列表 |
| revision_action | string\|null | 返工原因 |
| checked_at | string | 检查时间（ISO 8601）|

**说明**：完整指标保存在 `validation/validation.json`，`modeling/index.json` 只保存摘要和指针，避免数据不一致。

**状态流转**：

- `model_solving` 最小运行失败 → `model_establishment` / `model_solving`
- `model_validation` 对比失败 → `model_design` / `model_establishment` / `model_solving`

### validation/validation.json 结构

```json
{
  "validation_id": "V1",
  "protocol_path": "validation/plan.json",
  "protocol_hash": "sha256:...",
  "primary_model_ids": ["M1"],
  "baseline_model_ids": ["B1"],
  "run_ids": ["run-primary", "run-baseline"],
  "evaluations": [
    {
      "model_id": "M1",
      "metrics": {
        "rmse": 8.2,
        "runtime_seconds": 12.5
      }
    },
    {
      "model_id": "B1",
      "metrics": {
        "rmse": 11.6,
        "runtime_seconds": 4.8
      }
    }
  ],
  "criteria_results": [
    {
      "criterion_id": "C1",
      "observed": 8.2,
      "passed": true,
      "required": true
    }
  ],
  "comparisons": [
    {
      "metric": "rmse",
      "primary_model_id": "M1",
      "baseline_model_id": "B1",
      "primary_value": 8.2,
      "baseline_value": 11.6,
      "absolute_delta": -3.4,
      "relative_improvement": 0.2931,
      "same_protocol": true
    }
  ],
  "stability_results": [],
  "domain_results": [],
  "passed": true,
  "evidence_paths": [
    "validation/validation.md",
    "validation/comparison.md",
    "validation/sensitivity.md"
  ],
  "revision_action": null,
  "checked_at": ""
}
```

**字段说明**：

- `evaluations`：评估结果数组，每个元素包含 `model_id` 和 `metrics` 对象
- `comparisons`：对比结果数组，所有字段必须填写，数值从 evaluations 重新计算
- `baseline_exemption`：基线豁免信息（存在于 validation/plan.json）

### references

```json
[
  {
    "id": "ref-001",
    "title": "",
    "status": "verified|pending|unverifiable",
    "used_in": []
  }
]
```

### paper_sections

```json
[
  {
    "section": "摘要",
    "path": "paper/sections/abstract.md",
    "status": "draft|completed"
  }
]
```

### paper_deliverables

```json
{
  "markdown": {
    "path": "paper/final.md",
    "status": "pending|completed",
    "content_hash": "sha256:..." | null
  },
  "docx": {
    "path": "paper/final.docx",
    "status": "pending|completed",
    "build_record": "paper/build/docx-build.json",
    "content_hash": "sha256:..." | null
  },
  "latex": {
    "project_path": "paper/latex",
    "main_tex": "paper/latex/main.tex",
    "status": "pending|completed",
    "build_record": "paper/build/latex-build.json"
  },
  "pdf": {
    "path": "paper/final.pdf",
    "status": "pending|completed",
    "source": "latex",
    "build_record": "paper/build/latex-build.json",
    "content_hash": "sha256:..." | null
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| markdown.path | string | Markdown 论文路径 |
| markdown.status | string | 状态：pending/completed |
| markdown.content_hash | string\|null | 内容哈希（用于一致性检查）|
| docx.path | string | Word 论文路径 |
| docx.status | string | 状态：pending/completed |
| docx.build_record | string | 构建记录路径 |
| docx.content_hash | string\|null | 内容哈希 |
| latex.project_path | string | LaTeX 项目目录 |
| latex.main_tex | string | 主文件路径 |
| latex.status | string | 状态：pending/completed |
| latex.build_record | string | 构建记录路径 |
| pdf.path | string | PDF 文件路径 |
| pdf.status | string | 状态：pending/completed |
| pdf.source | string | 来源，固定为 "latex" |
| pdf.build_record | string | 构建记录路径（同 latex）|
| pdf.content_hash | string\|null | PDF 哈希（与构建记录一致）|

### blockers

```json
[
  {
    "id": "B1",
    "phase": "",
    "reason": "",
    "evidence": [],
    "requires_user": false,
    "question": "",
    "status": "open|resolved"
  }
]
```

仅 `requires_user: true` 且 `status: "open"` 的阻塞项允许 Agent 暂停询问用户。

### phase_gates

```json
{
  "intake": {
    "status": "pending|passed|failed",
    "checked_at": null,
    "evidence_paths": [],
    "input_hashes": {},
    "invalidated_at": null,
    "invalidated_reason": null
  },
  "problem_analysis": { /* 同上 */ },
  "literature_research": { /* 同上 */ },
  "model_design": { /* 同上 */ },
  "model_establishment": { /* 同上 */ },
  "model_solving": { /* 同上 */ },
  "model_validation": { /* 同上 */ },
  "result_interpretation": { /* 同上 */ },
  "paper_writing": { /* 同上 */ },
  "paper_build": { /* 同上 */ },
  "final_audit": { /* 同上 */ }
}
```

### completion_audit

```json
{
  "passed": false,
  "checked_at": null,
  "evidence": [],
  "missing_items": []
}
```

### last_updated

- **类型**：字符串（ISO 8601 时间戳）或 null

## 状态流转

```
intake
  → problem_analysis (门禁通过)
  → literature_research (门禁通过)
  → model_design (门禁通过)
  → model_establishment (门禁通过)
  → model_solving (门禁通过)
  → model_validation (门禁通过)
  → result_interpretation (门禁通过)
  → paper_writing (门禁通过)
  → paper_build (门禁通过)
  → final_audit (通过)
  → completed
```

返工：
- `model_validation` → `model_design` / `model_solving`
- `result_interpretation` → `model_solving`
- `final_audit` → `result_interpretation` / `paper_writing` / `paper_build` / `literature_research`

## 最小合法示例

```json
{
  "schema_version": 2,
  "project": {
    "name": "示例项目",
    "type": "math-modeling",
    "problem_type": [],
    "deadline": null
  },
  "research_policy": {
    "rules_checked": false,
    "network_allowed": true,
    "external_sources_allowed": true,
    "constraint_source": null
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
    "markdown": { "status": "pending" },
    "docx": { "status": "pending", "build_record": "paper/build/docx-build.json" },
    "latex": { "project_path": "paper/latex", "main_tex": "paper/latex/main.tex", "status": "pending", "build_record": "paper/build/latex-build.json" },
    "pdf": { "status": "pending", "source": "latex", "build_record": "paper/build/latex-build.json" }
  },
  "blockers": [],
  "next_actions": [],
  "phase_gates": {
    "intake": {
      "status": "pending",
      "checked_at": null,
      "evidence_paths": [],
      "input_hashes": {},
      "invalidated_at": null,
      "invalidated_reason": null
    },
    "problem_analysis": {
      "status": "pending",
      "checked_at": null,
      "evidence_paths": [],
      "input_hashes": {},
      "invalidated_at": null,
      "invalidated_reason": null
    },
    "literature_research": {
      "status": "pending",
      "checked_at": null,
      "evidence_paths": [],
      "input_hashes": {},
      "invalidated_at": null,
      "invalidated_reason": null
    },
    "model_design": {
      "status": "pending",
      "checked_at": null,
      "evidence_paths": [],
      "input_hashes": {},
      "invalidated_at": null,
      "invalidated_reason": null
    },
    "model_establishment": {
      "status": "pending",
      "checked_at": null,
      "evidence_paths": [],
      "input_hashes": {},
      "invalidated_at": null,
      "invalidated_reason": null
    },
    "model_solving": {
      "status": "pending",
      "checked_at": null,
      "evidence_paths": [],
      "input_hashes": {},
      "invalidated_at": null,
      "invalidated_reason": null
    },
    "model_validation": {
      "status": "pending",
      "checked_at": null,
      "evidence_paths": [],
      "input_hashes": {},
      "invalidated_at": null,
      "invalidated_reason": null
    },
    "result_interpretation": {
      "status": "pending",
      "checked_at": null,
      "evidence_paths": [],
      "input_hashes": {},
      "invalidated_at": null,
      "invalidated_reason": null
    },
    "paper_writing": {
      "status": "pending",
      "checked_at": null,
      "evidence_paths": [],
      "input_hashes": {},
      "invalidated_at": null,
      "invalidated_reason": null
    },
    "paper_build": {
      "status": "pending",
      "checked_at": null,
      "evidence_paths": [],
      "input_hashes": {},
      "invalidated_at": null,
      "invalidated_reason": null
    },
    "final_audit": {
      "status": "pending",
      "checked_at": null,
      "evidence_paths": [],
      "input_hashes": {},
      "invalidated_at": null,
      "invalidated_reason": null
    }
  },
  "completion_audit": {
    "passed": false,
    "checked_at": null,
    "evidence": [],
    "missing_items": []
  },
  "last_updated": null
}
```
