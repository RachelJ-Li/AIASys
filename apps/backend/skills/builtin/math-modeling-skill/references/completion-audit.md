# 完整性审计参考

适用于最终一致性检查与完成审计阶段。

## 目录

1. [审计范围](#审计范围)
2. [检查项](#检查项)
3. [审计失败处理](#审计失败处理)
4. [审计报告模板](#审计报告模板)
5. [完成状态更新](#完成状态更新)

## 审计范围

审计所有前序阶段的交付文件和状态记录。

## 检查项

### 1. 文件完整性

检查以下目录和文件是否存在且非空：

- `statement/problem.md`
- `statement/requirements.md`
- `statement/constraints.md`
- `data/raw/`
- `analysis/problem_analysis.md`
- `analysis/data_profile.md`
- `research/references.json`
- `model/<model_id>/formulation.md`
- `model/<model_id>/algorithm.md`
- `model/<model_id>/model.json`
- `runs/<run_id>/run.json`
- `runs/<run_id>.log`
- `runs/` 或 `results/tables/`
- `analysis/validation.md`
- `analysis/results.md`
- `paper/outline.md`
- `paper/final.md`
- `paper/references.md`

### 2. 论文交付物专项检查

#### 2.1 Markdown 论文

- `paper/final.md` 存在、非空且不含占位符
- 正文、结果、图表和参考文献一致

#### 2.2 Word 论文

- `paper/final.docx` 存在且为有效 OOXML（ZIP）格式
- 文件包含有效的 `[Content_Types].xml` 和 `word/document.xml`
- `word/document.xml` 包含非空正文内容

#### 2.3 LaTeX 项目

- `paper/latex/main.tex` 存在
- 所有 `\input`/`\include` 引用的文件存在
- 所有 `\includegraphics` 引用的图片存在（在 `paper/latex/figures/` 或 `paper/latex/tables/`）
- 所有 `\cite`/`\bibliography` 引用的参考文献条目存在
- LaTeX 项目包含完整资源和样式文件

#### 2.4 PDF 论文

- `paper/final.pdf` 存在且可读（文件大小合理，至少 100 字节）
- PDF 文件头以 `%PDF` 开头
- PDF 至少包含一页（如果安装了 pypdf 或 PyMuPDF）
- PDF 哈希与 `paper/build/latex-build.json` 中的 `pdf_sha256` 一致
- `paper/build/latex-build.json` 的 `status` 字段为 `"succeeded"`
- `paper/build/latex-build.json` 的 `source_hashes` 与当前 `paper/latex/` 源码哈希一致
- `source_hashes` 必须包含 `main.tex`
- PDF 由当前 LaTeX 源码编译生成（不是旧 PDF 或从别处复制）

#### 2.5 构建证据

- `paper/build/docx-build.json` 存在且包含必需字段：
  - `status`、`tool`、`command`、`return_code`、`docx_path`、`started_at`、`finished_at`
- `paper/build/latex-build.json` 存在且包含必需字段：
  - `status`、`engine`、`command`、`return_code`、`main_tex`、`source_hashes`、`pdf_path`、`pdf_sha256`、`log_path`、`started_at`、`finished_at`
- `paper/build/latex-compile.log` 存在且不包含致命编译错误
- `paper/content-manifest.json` 存在且包含：
  - 图表索引（figures）
  - 引用索引（citations）
  - 结论索引（claims）

### 3. 状态完整性

检查 `modeling/index.json`：

- `schema_version` 存在且为数字
- `project.type` 和 `project.problem_type` 已填写
- `current_phase` 为 `final_audit`
- `subproblems` 已登记且每个子问题有状态
- `selected_models` 已登记
- `runs` 至少有一个成功运行
- `validations` 至少有一个通过检验
- `paper_deliverables` 存在且包含四种格式的状态
- `completion_audit.passed` 必须由校验器根据真实证据计算，不依赖预先设置

### 4. 运行证据

- 每个成功运行具有日志文件（`log_paths` 非空）
- 每个成功运行具有结果文件（`result_paths` 非空）
- 运行记录的 `status = "succeeded"`
- 运行记录包含 `random_seed`、`command`、`reproduce_command`

### 5. 检验引用

- 每个检验记录引用的运行 ID 真实存在
- 检验记录引用的模型 ID 已登记
- 检验的 `passed = true`

### 6. 门禁失效检查

检查最近通过的门禁是否被输入变化失效：

- 运行记录的 `input_hashes` 与实际输入文件哈希对比
- 若不一致且 `invalidated_at` 未登记，标记为失效

### 7. 图片和引用链接

检查 `paper/final.md` 中的本地图片路径：

- 图片文件存在且可读
- 图片路径位于项目目录内（不包含 `..`、绝对路径或符号链接逃逸）

检查参考文献引用：

- 正文中的引用编号在 `references.md` 中存在对应条目
- `research/references.json` 中的 `status = "verified"`

### 8. 内容一致性检查

检查四种格式的内容一致性：

- Word、LaTeX 和 PDF 的核心结论与 Markdown 主稿一致
- 图表编号和引用在四种格式中连续且一致
- 公式和数值与代码结果一致
- 参考文献与正文引用双向对应

### 9. 审计失败处理

审计失败时：

- 不得将项目标记为完成
- `completion_audit.passed` 必须保持 `false`
- `project.status` 必须恢复为 `active`
- 生成审计报告文件 `audit/completion_report.md` 列出缺失项和无效项（分开呈现）

## 审计报告模板

保存到 `audit/completion_report.md`：

```markdown
# 完整性审计报告

- 审计时间：
- 项目状态：

## 审核结果

**总体结论**：

## 已验证证据

- 证据 1

## 缺失项

- 缺失项 1

## 无效项

- 无效项 1

## 阶段检查详情

| 阶段 | 状态 | 缺失 | 无效 |
|------|------|------|------|

## 警告

- 警告 1

## 审计结论

- 通过 / 未通过
```

## 完成状态更新

审计通过后更新 `modeling/index.json`：

```json
{
  "status": "completed",
  "current_phase": "final_audit",
  "paper_deliverables": {
    "markdown": {
      "path": "paper/final.md",
      "status": "completed",
      "content_hash": "sha256:..."
    },
    "docx": {
      "path": "paper/final.docx",
      "status": "completed",
      "build_record": "paper/build/docx-build.json",
      "content_hash": "sha256:..."
    },
    "latex": {
      "project_path": "paper/latex",
      "main_tex": "paper/latex/main.tex",
      "status": "completed",
      "build_record": "paper/build/latex-build.json"
    },
    "pdf": {
      "path": "paper/final.pdf",
      "status": "completed",
      "source": "latex",
      "build_record": "paper/build/latex-build.json",
      "content_hash": "sha256:..."
    }
  },
  "completion_audit": {
    "passed": true,
    "checked_at": "",
    "evidence": ["..."],
    "missing_items": []
  }
}
```

## 进入下一阶段

审计通过即为完成，项目状态更新为 `completed`。

## 暂停条件

- 自动修复后仍存在只能由用户补充的必要信息
- 交付规则存在无法消解的冲突
