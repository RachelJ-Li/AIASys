# 模型设计参考

适用于假设定义、符号规范和模型选择阶段。

## 假设设计

### 假设要求

1. **可解释**：说明假设的依据和来源
2. **可检验**：可通过数据或实验验证
3. **必要**：不假设不会简化问题
4. **无矛盾**：假设之间不矛盾，且不与题目约束冲突

### 假设模板

```markdown
## 假设清单

| 编号 | 假设内容 | 依据 | 检验方法 |
|------|----------|------|----------|
| H1 | [假设描述] | [理论/经验依据] | [检验思路] |
```

## 符号与量纲

### 符号定义规则

- 使用标准数学符号
- 同一符号在全文中含义一致
- 向量和矩阵需明确区分
- 下标和上标需说明

### 符号模板

```markdown
## 符号说明

| 符号 | 含义 | 单位 | 类型 |
|------|------|------|------|
| x | [描述] | [单位] | 标量/向量/矩阵 |
```

### 量纲一致性检查

- 公式两边的量纲必须一致
- 参数的单位必须合理
- 输入输出的量纲必须匹配

## 候选模型比较

### 比较维度

1. **适用性**：匹配问题类型和数据特征
2. **预测或求解性能**：预期准确率、误差或求解质量
3. **可验证性**：是否有明确的验证方法和基线
4. **稳健性**：对数据和参数变化的敏感程度
5. **可解释性**：结果是否易于理解和说明
6. **计算资源**：时间、内存和算力需求

### 比较模板

```markdown
## 候选模型比较

| 模型 | 角色 | 适用性 | 预期性能 | 稳健性 | 可解释性 | 计算成本 | 验证方式 |
|------|------|--------|----------|--------|----------|----------|----------|
| [模型A] | primary/baseline | [评分] | [评分] | [评分] | [评分] | [评分] | [方法] |

**选择**：[模型X]，理由：
```

## 模型选择决策

```json
{
  "model_id": "M1",
  "subproblem_ids": ["P1"],
  "family": "optimization",
  "role": "primary",
  "baseline_model_ids": ["B1"],
  "selection_reason": "",
  "formulation_path": "model/M1/formulation.md",
  "algorithm_path": "model/M1/algorithm.md",
  "config_path": "configs/M1.json",
  "validation_plan_path": "validation/plan.json",
  "status": "selected"
}
```

**基线模型**（role=baseline）：

```json
{
  "model_id": "B1",
  "subproblem_ids": ["P1"],
  "family": "optimization",
  "role": "baseline",
  "baseline_for": ["M1"],
  "formulation_path": "model/B1/formulation.md",
  "algorithm_path": "model/B1/algorithm.md",
  "config_path": "configs/B1.json",
  "status": "selected"
}
```

**基线豁免**：确实无法设置基线时，不允许只留空，应登记：

```json
{
  "required": false,
  "reason": "不存在可运行的同类基线",
  "evidence_paths": ["model/selection.md"],
  "alternative": "解析解对比与消融实验"
}
```

## 模型建立规范

### 公式表达

- 使用 LaTeX 语法（Markdown 数学公式支持）
- 每个公式编号（如式 (1)）
- 变量首次出现时定义

### 配置文件

```json
{
  "model_id": "M1",
  "description": "",
  "parameters": {
    "param1": {
      "type": "float",
      "default": 0.0,
      "range": [0, 1],
      "description": ""
    }
  },
  "inputs": {
    "data_path": "data/processed/cleaned.csv",
    "format": "csv"
  },
  "outputs": {
    "result_path": "runs/<run_id>/results.json",
    "format": "json"
  },
  "solver": {
    "type": "",
    "options": {}
  }
}
```

## 进入下一阶段的条件

- 假设、符号和模型选择文件已创建
- 每个主模型均有基线模型或有效豁免
- 每个子问题已确定验证类型

## 暂停条件

- 题目约束与数据矛盾，候选模型均不可用
- 关键目标权重或风险阈值必须由用户决定
- 高影响假设无依据且无法通过检验控制风险
