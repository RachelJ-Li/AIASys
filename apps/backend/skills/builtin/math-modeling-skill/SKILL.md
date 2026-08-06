+++
name = "数学建模"
description = "用于数学建模任务的问题分析、模型建立、编程求解、模型检验、结果可视化和论文撰写。适用于用户提供赛题、数据或建模任务，希望 Agent 自主完成完整建模流程、多格式论文交付或继续某个建模环节的场景。"
+++

# 数学建模 Skill

驱动 Agent 完成通用数学建模任务的全流程 SOP。

## 何时使用

- 提供赛题、数据或建模任务，要求 Agent 自主完成
- 希望继续或恢复已有的建模项目
- 需要完成建模的某个特定环节

## 何时不使用

- 只需要普通文章润色且不涉及建模
- 只需要简单算术或单个公式计算
- 只要求读取现有论文，不需要建立或求解模型
- 纯数据竞赛 baseline 优化应优先使用 competition 系列 Skill

## 工作区根目录与安全规则

- 工作区根目录：从环境变量 `AIASYS_WORKSPACE_ROOT` 获取
- 所有路径操作必须限制在工作区根目录内
- `statement/` 和 `data/raw/` 视为原始只读材料，不得修改
- 派生数据只能写入 `data/processed/`
- 不伪造数据、程序执行、模型指标、图表、引用或论文来源

## 初始化与恢复

```bash
# 从零开始
python scripts/init_project.py

# 恢复已有项目（直接读取 modeling/index.json）
```

## 流程路由

11 个阶段详见 `references/workflow.md`。按需加载：

| 阶段 | 参考文档 |
|------|----------|
| 材料接收 | `references/workflow.md#intake` |
| 问题分析 | `references/workflow.md#problem_analysis` |
| 文献检索 | `references/workflow.md#literature_research` |
| 模型设计 | `references/workflow.md#model_design` |
| 模型建立 | `references/workflow.md#model_establishment` |
| 编程求解 | `references/workflow.md#model_solving` |
| 模型检验 | `references/workflow.md#model_validation` |
| 结果解释 | `references/workflow.md#result_interpretation` |
| 论文撰写 | `references/workflow.md#paper_writing` |
| 多格式构建 | `references/workflow.md#paper_build` |
| 完成审计 | `references/workflow.md#final_audit` |

通用规范：
- `references/schema.md`：`modeling/index.json` 字段定义
- `references/problem-analysis.md`：题目解析、数据检查
- `references/literature-research.md`：检索、筛选、引用规范
- `references/model-design.md`：假设、符号、选模规范
- `references/model-solving.md`：代码、配置、运行、结果规范
- `references/model-validation.md`：检验、敏感性、回退规范
- `references/paper-writing.md`：Markdown 论文写作规范
- `references/completion-audit.md`：最终完整性审计规范

## 强制门禁

每个阶段完成后必须校验：

```bash
python scripts/validate_project.py --phase <阶段> --json
```

- 门禁未通过时不得进入下一阶段
- 最小可运行验证：必须先跑通 `数据读取 → 预处理 → 核心模型 → 结果写出`
- 成功运行必须具有真实命令、日志和结果文件
- 输入变化后相关门禁失效，必须重新校验

## 模型验证强制规则

- 在模型全量求解前必须创建 `validation/plan.json`，预先定义主模型、基线模型、统一实验口径、评价指标和通过条件
- 模型验证必须包含必要条件判断、基线对比、稳定性检查和适用问题类型要求的领域检查
- `validation/validation.json` 中的整体结果由校验器根据实际指标计算，不得由 Agent 直接填写 passed 字段
- 按问题类型选择标准验证方法：`references/validation-profiles.md`

## 完成判定

- `completion_audit.passed = true`
- 所有必需文件存在且非空
- 所有子问题状态为完成
- 所有运行、检验、图表和引用可追溯
- `paper/final.md` 存在并满足提交要求
- `paper/final.docx` 存在且为有效 OOXML 格式
- `paper/latex/` 存在且包含完整 LaTeX 项目
- `paper/final.pdf` 存在且由当前 LaTeX 源码编译生成
- `paper/build/docx-build.json` 存在且构建成功
- `paper/build/latex-build.json` 存在且构建成功

最终审计：`python scripts/validate_project.py --all --record --json`
