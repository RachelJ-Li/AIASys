# 模型验证参考

适用于模型检验与敏感性分析阶段。

## 验证原则

- 验证结果由校验器根据实际指标计算，不得由 Agent 直接声明
- 必须包含基线或候选模型对比
- 必须根据问题类型选择标准验证方法（参见 `validation-profiles.md`）
- 必须验证性能、稳定性、约束、资源和适用性
- 不得只检查文件存在，必须读取并验证实际指标

## 验证计划

模型求解前必须创建 `validation/plan.json`，预先定义：

```json
{
  "plan_id": "VP1",
  "problem_type": ["optimization", "prediction"],
  "primary_model_ids": ["M1"],
  "baseline_model_ids": ["B1"],
  "baseline_exemption": null,
  "protocol": {
    "dataset_version": "data/processed/cleaned.csv",
    "dataset_split_id": "split-001",
    "train_ratio": 0.7,
    "validation_ratio": 0.15,
    "test_ratio": 0.15,
    "random_seeds": [42, 43, 44],
    "preprocessing_steps": ["normalization", "outlier_removal"]
  },
  "criteria": [
    {
      "criterion_id": "C1",
      "subproblem_id": "P1",
      "model_id": "M1",
      "metric": "rmse",
      "direction": "minimize",
      "operator": "<=",
      "threshold": 10.0,
      "source": "赛题要求",
      "required": true
    }
  ]
}
```

### criterion 与 model_id 的对应关系

- `criterion_id`：全局唯一标识符
- `subproblem_id`：关联的子问题 ID
- `model_id`：评估哪个模型的指标，默认 primary_model_ids[0]
- `metric`：评价指标名称
- `direction`：优化方向（minimize / maximize / target / boolean）
- `operator`：比较运算符（< / <= / > / >= / == / between）
- `threshold`：阈值，between 时为 [min, max]
- `source`：阈值来源（赛题 / 文献 / 数据 / 基线）
- `required`：是否为必要条件（默认 true）

### 所有汇总状态由校验器计算

以下状态必须由校验器根据实际指标计算，不得由 Agent 直接填写：

- `criteria_results`：根据 evaluations 数组计算各条件实测值和通过状态
- `criteria_passed`：所有 required criteria 通过
- `comparison_passed`：基线对比通过
- `stability_passed`：稳定性验证通过
- `domain_checks_passed`：领域验证通过
- `passed`：整体通过状态

### 基线豁免存放位置

baseline_exemption 统一登记在 `validation/plan.json` 顶层：

```json
{
  "baseline_exemption": {
    "reason": "不存在可运行的同类基线",
    "evidence_paths": ["model/selection.md"],
    "alternative": "解析解对比与消融实验",
    "required": false
  }
}
```

豁免必须包含：
- `reason`：豁免原因（必填）
- `evidence_paths`：证据文件路径（必填）
- `alternative`：替代验证方案（必填）
- `required`：是否强制豁免（默认 false）

### comparisons 必需字段

每个对比项必须包含以下字段：

```json
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
```

- `primary_value` 和 `baseline_value` 必须从 `evaluations` 数组重新计算，不得仅信任预填值
- `same_protocol` 由校验器根据协议哈希和数据集划分判断

## 判断条件

### 必要字段

每项判断条件至少包含：

```json
{
  "criterion_id": "C1",
  "subproblem_id": "P1",
  "metric": "rmse",
  "direction": "minimize",
  "operator": "<=",
  "threshold": 10.0,
  "source": "赛题要求",
  "required": true
}
```

### 合法方向

- `minimize`：越小越好
- `maximize`：越大越好
- `target`：越接近目标值越好
- `boolean`：布尔判断（通过/失败）

### 合法运算符

- `<`、`<=`、`>`、`>=`、`==`
- `between`：区间判断（threshold 为 [min, max]）

### 评估规则

- `criteria` 不能为空
- `required=true` 的条件必须全部通过
- 阈值必须来自赛题、文献、数据分析或模型合同
- 方向、运算符、阈值必须合法

## 统一比较

主模型和基线模型必须使用相同验证协议：

- 相同数据版本
- 相同训练、验证或测试划分
- 相同预处理
- 相同随机种子集合
- 相同评价指标
- 可比的运行资源和参数预算

比较至少包括：

- 主要性能指标
- 稳定性
- 约束满足情况
- 运行时间
- 资源消耗
- 可解释性或适用性

## 稳定性与敏感性

根据问题类型选择标准验证方法（参见 `validation-profiles.md`）。

### 参数扰动

- 选择关键参数
- 在合理范围内扰动
- 观察输出变化

保存到 `validation/sensitivity.md`：

```markdown
## 敏感性分析报告

### 参数扰动结果

| 参数 | 基准值 | 扰动幅度 | 输出变化 | 敏感程度 |

### 稳定性结论

- [结论 1]
```

### 稳健性检查

- 输入数据微小变化是否显著影响结果
- 极端场景是否仍合理
- 关键假设放宽后结果是否稳定

## 领域验证

根据 `validation/plan.json` 中 `problem_type` 选择验证维度：

- 优化模型：可行率、目标函数值、收敛性
- 回归预测：MAE、RMSE、MAPE、R²、交叉验证
- 分类模型：Precision、Recall、F1、ROC-AUC、混淆矩阵
- 时间序列：滚动验证、预测误差、残差自相关
- 聚类：轮廓系数、聚类稳定性
- 微分方程：数值收敛、守恒关系、解析解对比
- 生物模型：统计显著性、多重检验校正、生物学合理性

## 验证结果结构

`validation/validation.json` 建议结构：

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
      "passed": true
    }
  ],
  "comparisons": [
    {
      "metric": "rmse",
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

**说明**：

- `passed` 必须由校验器根据实际指标计算并覆盖，不得由 Agent 直接填写
- 完整数值只保存在 `validation/validation.json`，`modeling/index.json` 只保存摘要
- `evaluations` 必须包含主模型和基线模型的真实运行指标

### 计算结果

整体通过条件：

```
所有 required criteria 通过
且 comparison_passed
且 stability_passed
且 domain_checks_passed
```

存在有效基线豁免时，`comparison_passed` 改由替代验证结果决定。

## 返工机制

检验失败时：

1. 记录失败原因
2. 返回相应前序阶段：
   - 约束不满足 → 返回模型建立
   - 结果不合理 → 返回求解环节
   - 方法不当 → 返回文献检索或模型选择
3. 修复后重新登记运行和检验

返工记录必须包含：
- `revision_action`：返工原因
- `revision_target`：返回的阶段

## 进入下一阶段的条件

- 所有必要条件通过
- 对比验证通过
- 稳定性验证通过
- 领域验证通过（如适用）
- 验证结果由校验器计算，不是 Agent 填写

## 暂停条件

- 多轮返工后所有模型仍无法通过检验
- 修复需要新数据或变更任务目标
- 评价口径冲突且会改变结论
- 基线无法设置且无有效替代验证方案
