# 数学建模工作流

完整定义 11 个阶段（正式流程）的五项契约：输入、Agent执行、输出文件、进入下一流程的条件、暂停条件。

统一路径规范（参见 `schema.md`）：

```
statement/
data/raw/
data/processed/
analysis/
research/notes/
model/
model/<model_id>/
src/<model_id>/
configs/
runs/<run_id>/
validation/
results/summary.md
results/figures/
results/tables/
paper/outline.md
paper/final.md
paper/references.md
paper/final.docx
paper/latex/
paper/final.pdf
paper/sections/
paper/build/docx-build.json
paper/build/latex-build.json
paper/build/latex-compile.log
paper/content-manifest.json
audit/completion_report.md
modeling/index.json
```

---

## 1. 材料接收与规则核验 (intake)

### 输入

- 用户首次提供的赛题或任务说明
- 用户首次提供的数据和附件
- 用户首次提供的提交格式、截止时间、篇幅和特殊规则

### Agent执行

1. 读取并归档题面、附件和数据
2. 提取任务目标、提交要求和约束
3. 核验联网、外部数据和 AI 使用规则
4. 更新项目状态

### 输出文件

- `statement/problem.md`：赛题原文/翻译
- `statement/requirements.md`：提交要求、格式规范
- `statement/constraints.md`：假设条件、赛题约束、工具限制
- `data/raw/*`：原始数据与附件
- 更新 `modeling/index.json`：
  - `project.type`：竞赛类型
  - `project.problem_type`：问题类型
  - `project.deadline`：截止时间
  - `research_policy`：联网与外部资料策略

### 进入下一流程的条件

- 题面、要求、约束和原始材料已归档
- 项目信息与联网策略已登记
- 所有必需文件已存在、非空且不含占位符
- `project.type`、`project.problem_type`、`research_policy.rules_checked` 已填写

### 暂停并询问用户的条件

- 缺少关键题面、附件或数据，且无法自行获得
- 文件损坏、加密或无权限读取
- 赛题规则存在影响提交资格的冲突

---

## 2. 问题理解与拆解 (problem_analysis)

### 输入

- `statement/problem.md`
- `statement/requirements.md`
- `statement/constraints.md`
- `data/raw/*`
- `modeling/index.json` 中的 `project` 与 `research_policy`

### Agent执行

1. 重述问题并拆分子问题
2. 明确输入、输出、变量、约束和评价指标
3. 检查数据字段、缺失值和异常值
4. 清洗数据并登记处理过程

### 输出文件

- `analysis/problem_analysis.md`：问题重述、子问题拆解
- `analysis/data_profile.md`：数据字段、质量与可用性
- `data/processed/*`：清洗或转换后的数据
- 更新 `modeling/index.json`：
  - `subproblems`：子问题、依赖和验收条件

### 进入下一流程的条件

- 问题和数据分析文件已创建
- 所有题目要求均已映射到子问题
- 子问题列表已登记且非空

### 暂停并询问用户的条件

- 题目存在影响任务目标的关键歧义
- 必需字段缺失且无法推导或替代
- 数据错误无法自动修复，需要确认版本

---

## 3. 文献与资料检索 (literature_research)

### 输入

- `analysis/problem_analysis.md`
- `analysis/data_profile.md`
- `statement/constraints.md`
- `modeling/index.json` 中的 `subproblems` 与 `research_policy`

### Agent执行

1. 检索论文、官方资料和可信数据
2. 提取方法、假设、指标和验证思路
3. 核验并登记来源

### 输出文件

- `research/notes/*`：文献与资料笔记
- `research/references.json`：参考来源及核验信息
- `paper/references.md`：Markdown 参考文献表
- 更新 `modeling/index.json`：
  - `references`：来源 ID、状态和使用位置

### 进入下一流程的条件

- 每个核心子问题有方法依据或明确的自主推导路径
- 参考文献来源可追溯
- 联网行为符合赛题规则

### 暂停并询问用户的条件

- 赛题禁止完成任务所必需的联网或外部资料
- 必需资料受权限或付费限制，且无公开替代
- 外部数据许可无法确认

---

## 4. 假设、符号与候选模型 (model_design)

### 输入

- `analysis/problem_analysis.md`
- `analysis/data_profile.md`
- `data/raw/*`
- `modeling/index.json` 中的 `subproblems` 与 `research_policy`

### Agent执行

1. 提出假设并说明依据
2. 定义符号和单位
3. 比较候选模型（预测或求解性能、可验证性、基线角色、计算资源）
4. **确定每个子问题的主模型和基线模型**
5. 选择主模型和验证方法

### 输出文件

- `model/assumptions.md`：建模假设及依据
- `model/notation.md`：符号、含义和单位
- `model/candidates.md`：候选模型比较（含角色、验证方式）
- `model/selection.md`：主模型、基线模型和选择理由
- 更新 `modeling/index.json`：
  - `assumptions`：假设记录
  - `notations`：符号记录
  - `model_candidates`：候选模型及状态
  - `selected_models`：主模型、基线模型列表及验证计划路径

### 进入下一流程的条件

- 假设、符号和模型选择文件已创建且不含占位符
- 每个主模型均有基线模型或有效豁免
- 每个子问题已确定验证类型
- `selected_models` 非空且含 role 字段

### 暂停并询问用户的条件

- 题目约束与数据矛盾，候选模型均不可用
- 关键目标权重或风险阈值必须由用户决定
- 高影响假设无依据且无法通过检验控制风险

---

## 5. 模型建立 (model_establishment)

### 输入

- `model/assumptions.md`
- `model/notation.md`
- `model/selection.md`
- `model/candidates.md`
- `analysis/problem_analysis.md`
- `modeling/index.json` 中的 `subproblems`、`selected_models`
- `references/validation-profiles.md`（按需读取）

### Agent执行

1. 建立模型公式、目标和约束
2. 说明推导、参数和现实对应关系
3. 登记求解方法、输出和验证方式
4. **根据模型类型读取 `references/validation-profiles.md`，预先定义评价指标、阈值、方向和依据**
5. **定义主模型与基线模型的统一实验口径**
6. **创建 `validation/plan.json`**

### 输出文件

- `model/<model_id>/formulation.md`：模型公式、目标与约束
- `model/<model_id>/algorithm.md`：求解方法与算法步骤
- `configs/<model_id>.json`：模型配置、输入输出和文件路径
- `validation/plan.json`：指标、阈值、基线和统一实验口径

### 进入下一流程的条件

- 每个选定模型的 formulation.md 和 algorithm.md 已创建且不含占位符
- `validation/plan.json` 已创建、可解析、criteria 非空
- 每项必要条件含指标、方向、阈值和来源
- 配置文件可解析
- 已定义成功判据和验证方式

### 暂停并询问用户的条件

- 约束导致模型无可行解，且不能自行调整
- 关键参数无法获得、估计或检验
- 不同建模口径对应不同任务目标

---

## 6. 编程求解与数值实验 (model_solving)

### 输入

- `model/<model_id>/formulation.md`
- `model/<model_id>/algorithm.md`
- `configs/<model_id>.json`
- `data/raw/` 与 `data/processed/`（适用时）
- `validation/plan.json`
- `modeling/index.json` 中的模型与运行配置

### Agent执行

1. 检查运行环境和依赖
2. 执行最小可运行验证
3. **最小链路通过后执行主模型和基线模型**
4. **所有模型使用相同数据、预处理、划分和评价口径**
5. 编写并执行可复现的 runner
6. 记录参数、随机种子、日志和退出码
7. 验证结果文件真实有效

### 输出文件

- `src/<model_id>/*`：求解代码
- `runs/<run_id>/run.json`：运行参数、环境和状态
- `runs/<run_id>/stdout.log`：标准输出日志
- `runs/<run_id>/stderr.log`：错误输出日志
- `runs/<run_id>/results.json`：结构化运行结果
- 更新 `modeling/index.json`：
  - `runs`：运行 ID、模型、状态、验证协议和产物路径

### 运行记录

每项 run.json 增加：

```json
{
  "model_role": "primary|baseline",
  "run_scope": "minimum|full",
  "minimum_gate_passed": true,
  "protocol_path": "validation/plan.json",
  "protocol_hash": "sha256:...",
  "dataset_split_id": "split-001"
}
```

### 进入下一流程的条件

- 最小可运行链路已通过（`minimum_gate_passed=true`）
- 主模型存在成功全量运行
- 必需基线存在成功全量运行（或存在有效豁免）
- 主模型和基线 `protocol_hash` 一致
- 主模型和基线 `dataset_split_id` 一致
- 所有比较运行引用相同验证协议
- 关键结果来自真实程序输出
- 运行记录可复现并引用现有文件

### 暂停并询问用户的条件

- 缺少必需的软件、凭据、算力或数据权限
- 预计资源消耗超出限制，需要用户授权
- 多次排错后仍需用户决定精度与成本取舍

---

## 7. 模型检验与敏感性分析 (model_validation)

### 输入

- `validation/plan.json`
- `runs/<run_id>/run.json`
- `runs/<run_id>/results.json`
- `model/<model_id>/formulation.md`
- `modeling/index.json`

### Agent执行

1. 根据 `validation/plan.json` 和 `references/validation-profiles.md` 选择验证方法
2. 执行误差、边界、稳健性或敏感性分析
3. 创建 `validation/validation.json` 和 `validation/comparison.md`
4. **校验器根据实际指标计算结果，不得由 Agent 直接填写 passed**
5. 检验失败时自动返回建模或求解环节

### 输出文件

- `validation/validation.md`：检验方法、指标和结果
- `validation/comparison.md`：主模型与基线模型对比结果
- `validation/sensitivity.md`：参数敏感性与稳健性结果
- `validation/validation.json`：结构化验证记录（由校验器生成 passed 字段）
- 更新 `modeling/index.json`：
  - `validations`：验证摘要、证据和返工记录（不重复保存完整指标）

### 验证规则

- 必须包含基线对比（或有效替代验证）
- 必须根据问题类型选择验证维度
- 必须验证性能、稳定性、约束、资源和适用性
- 不得只检查文件存在，必须读取并验证实际指标
- `validation/validation.json` 中 `passed` 字段由校验器计算并覆盖

### 进入下一流程的条件

- `validation/plan.json` 存在且有效
- 主模型和基线运行采用相同协议（`protocol_hash`、`dataset_split_id` 一致）
- 所有必要条件通过
- 对比验证通过
- 稳定性验证通过
- 领域验证通过（如适用）
- 验证结果由校验器计算

### 暂停并询问用户的条件

- 多轮返工后所有模型仍无法通过检验
- 修复需要新数据或变更任务目标
- 评价口径冲突且会改变结论
- 基线无法设置且无有效替代验证方案

---

## 8. 结果解释与可视化 (result_interpretation)

### 输入

- `runs/<run_id>/results.json`
- `validation/validation.md`
- `validation/comparison.md`
- `validation/sensitivity.md`（适用时）
- `modeling/index.json` 中已通过的 `validations`

### Agent执行

1. 汇总并解释各子问题结果
2. 解释主模型与基线的性能差异
3. 说明性能提升是否稳定
4. 说明未通过或没有明显提升的指标
5. 生成必要图表和表格
6. 标注来源、单位和生成脚本

### 输出文件

- `results/summary.md`：各子问题的结果与解释
- `results/figures/`：最终图表
- `results/tables/`：最终表格

### 进入下一流程的条件

- 所有子问题均有明确结果
- 结果解释与验证结论一致
- 不得只报告主模型的最佳结果
- 数字、图表和表格可追溯到运行记录

### 暂停并询问用户的条件

- 结果冲突且无法通过复现实验解决
- 结果解释依赖未登记的业务偏好或决策阈值

---

## 9. Markdown 文章撰写 (paper_writing)

### 输入

- `statement/*`
- `analysis/*`
- `research/*`
- `model/*`
- `validation/*`
- `results/*`
- `modeling/index.json`

### Agent执行

1. 生成文章大纲和章节草稿
2. 整合为 `paper/final.md`（结构化内容主稿）
3. 统一符号、公式、图表、表格、引用和结论
4. 准备 Word 和 LaTeX 共用的内容与资源
5. 检查结果、图表和引用一致性
6. **论文中的模型评价必须引用真实对比结果，不得只写"模型效果良好"而不提供基线和指标**

### 输出文件

- `paper/outline.md`：论文结构、章节要点和主张—证据映射
- `paper/sections/*.md`：分章节草稿
- `paper/final.md`：最终 Markdown 论文（主稿）
- `paper/references.md`：最终参考文献表
- 更新 `modeling/index.json`：
  - `paper_sections`：章节状态和文件路径
  - `paper_deliverables.markdown.status`：更新为 "completed"

### 进入下一流程的条件

- `paper/final.md` 已创建、非空且不含占位符
- 正文、结果、图表和参考文献一致
- 主张—证据映射完整
- `paper_deliverables.markdown.status` 已更新
- 论文模型评价部分引用 `validation/comparison.md` 的真实对比结果

### 暂停并询问用户的条件

- 作者、队伍编号等必填信息缺失
- 格式或署名规则冲突，可能影响提交

---

## 10. 多格式构建与发布 (paper_build)

### 输入

- `paper/final.md`
- `paper/references.md`
- `results/figures/`
- `results/tables/`
- `statement/requirements.md`
- `statement/constraints.md`
- `modeling/index.json`

### Agent执行

1. 检查赛题官方 Word 或 LaTeX 模板
2. 生成完整 Word 论文，保存为 `paper/final.docx`
3. 创建完整 LaTeX 源码项目，保存到 `paper/latex/`
4. 实际执行 LaTeX 编译，生成 `paper/final.pdf`
5. 保存编译命令、日志、退出码和哈希到构建证据文件
6. 检查 Markdown、Word、LaTeX 和 PDF 的内容一致性
7. 更新 `modeling/index.json` 中的 `paper_deliverables` 状态和论文产物索引

### 输出文件

- `paper/final.docx`：完整 Word 论文
- `paper/latex/`：完整 LaTeX 源码项目（含 `main.tex`、`sections/`、`figures/`、`tables/`、`references.bib` 等）
- `paper/final.pdf`：由 LaTeX 实际编译生成的 PDF
- `paper/build/docx-build.json`：Word 生成命令、工具和结果
- `paper/build/latex-build.json`：LaTeX 编译环境、命令和产物哈希
- `paper/build/latex-compile.log`：LaTeX 实际编译日志
- `paper/content-manifest.json`：各格式共享的图表、引用和结论索引
- 更新 `modeling/index.json`：
  - `paper_deliverables.docx.status`：更新为 "completed"
  - `paper_deliverables.latex.status`：更新为 "completed"
  - `paper_deliverables.pdf.status`：更新为 "completed"
  - `paper_deliverables.docx.build_record`：设置为 `paper/build/docx-build.json`
  - `paper_deliverables.latex.build_record`：设置为 `paper/build/latex-build.json`
  - `paper_deliverables.pdf.build_record`：设置为 `paper/build/latex-build.json`

### 进入下一流程的条件

- `paper/final.docx` 存在且为有效 DOCX 文件（OOXML ZIP 格式）
- `paper/latex/main.tex` 存在且项目包含完整依赖和资源
- LaTeX 编译退出码为 `0`
- `paper/final.pdf` 存在且来源可追溯到当前 LaTeX 源码
- Word、LaTeX 和 PDF 的核心结论、图表、公式和参考文献一致
- 构建日志、命令和哈希记录完整
- `paper_deliverables` 中所有状态已更新

### 暂停并询问用户的条件

- 官方模板或专用字体无法从现有材料和公开渠道获得
- 必需的专有编译环境、许可证或付费工具不可用
- 赛题同时提供多套互斥模板，无法判断应使用哪一套
- 自动安装、修复和替代编译方案均失败
- 用户必须提供学校、队伍、编号或署名信息

---

## 11. 一致性检查与完成审计 (final_audit)

### 输入

- `paper/final.md`
- `paper/final.docx`
- `paper/latex/`
- `paper/final.pdf`
- `paper/references.md`
- `paper/build/docx-build.json`
- `paper/build/latex-build.json`
- `paper/build/latex-compile.log`
- `paper/content-manifest.json`
- `statement/requirements.md`
- `modeling/index.json`
- `validation/plan.json`
- `validation/validation.json`
- `validation/comparison.md`
- 全部已登记产物

### Agent执行

1. 检查题目要求与交付物
2. 检查公式、单位、参数和数字
3. 检查运行、结果、正文和引用证据链
4. **检查验证结果**：
   - `validation/plan.json` 存在且有效
   - 主模型和基线运行采用相同协议
   - `validation/comparison.md` 存在
   - 所有必要条件有实测值
   - 整体验证状态由真实条件计算
   - 论文中的模型性能与 `validation/validation.json` 一致
   - 模型输入、运行或验证计划变化后，原验证门禁失效
5. **检查四种格式的内容一致性**：
   - Markdown、Word、LaTeX 和 PDF 的核心结论一致
   - 图表编号和引用连续且一致
   - 公式和数值与代码结果一致
   - 参考文献与正文引用双向对应
6. **检查构建证据**：
   - 4 个构建证据文件存在且完整
   - LaTeX 编译退出码为 0
   - PDF 哈希与构建记录一致
   - 源码哈希与构建时记录一致
7. 自动修复问题并生成审计结果

### 输出文件

- `audit/completion_report.md`：交付物检查结果
- 更新 `modeling/index.json`：
  - `completion_audit`：审计状态、缺失项和证据

### 完成条件

- 使用 `--all --record` 执行，由校验器根据真实证据计算审计结果
- 审计通过后由校验器写入 `completion_audit.passed = true`
- **所有四种格式均已完成**：`paper/final.md`、`paper/final.docx`、`paper/latex/` 和 `paper/final.pdf` 存在且有效
- 构建证据文件完整
- 所有子问题状态为完成
- 所有运行、检验、图表和引用可追溯
- 验证结果通过且由校验器计算
- Word、LaTeX、PDF 与 Markdown 主稿内容一致

### 暂停并询问用户的条件

- 自动修复后仍存在只能由用户补充的必要身份或授权信息
- 交付规则存在无法消解的冲突

---

验证失败或证据不足时：
1. 检查现有上游文件
2. 尝试重新生成
3. 尝试修复或回退
4. 使用可行的替代方案
5. 只有形成真实用户阻塞时才能询问用户

仅在 `modeling/index.json` 的 `blockers` 中存在 `requires_user: true` 且 `status: open` 的开放项时，Agent 才可暂停询问用户。

允许暂停的情形：
- 关键题目内容不可获得
- 互斥目标必须由用户选择
- 必需的身份、授权、凭证或付费操作需用户确认
- 赛题合规规则无法判断
- 所有合理自动修复和替代方案均失败
