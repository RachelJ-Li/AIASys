# 求解运行参考

适用于编程求解与数值实验阶段。

## 环境准备

### 工作区运行环境

- 数学建模代码必须使用工作区绑定的 UV/Python 环境
- 不修改 `apps/backend/.venv`（AIASys 后端环境）
- 依赖缺失时，通过运行环境管理能力安装到目标工作区环境

### 最小可运行验证

在全量运行前，必须先跑通最小可运行路径：

```
数据读取 → 数据预处理 → 核心模型 → 结果写出
```

可使用：
- 真实数据的小规模子集
- 结构等价的小实例

最小运行未成功时，不得进入全量运行。

## 代码结构

```
model/<model_id>/
├── code/
│   ├── solve.py         # 求解主脚本
│   ├── preprocess.py    # 数据预处理
│   └── visualize.py     # 可视化
├── formulation.md       # 模型公式
├── algorithm.md         # 算法步骤
└── model.json           # 模型配置
```

## 可复现性要求

### 随机种子

所有随机过程必须设置随机种子，并在运行记录中登记：

```python
import random
import numpy as np

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
```

### 统一实验协议

主模型和基线模型必须使用：

- 相同数据版本
- 相同训练、验证或测试划分
- 相同预处理
- 相同随机种子集合
- 相同评价指标
- 可比的运行资源和参数预算

### 最小运行门禁

在全量运行前必须先通过最小可运行验证，最小运行记录必须满足以下条件：

- `run_scope` = "minimum"
- `status` = "succeeded"
- `minimum_gate_passed` = true
- 包含 `command`、`log_paths`、`result_paths` 字段

最小运行记录示例：

```json
{
  "run_id": "run-minimum",
  "model_id": "M1",
  "status": "succeeded",
  "run_scope": "minimum",
  "minimum_gate_passed": true,
  "command": "python run_minimum.py",
  "log_paths": ["runs/run-minimum.log"],
  "result_paths": ["runs/run-minimum.json"],
}
```

只有 `minimum_gate_passed=true` 才能开始全量运行。校验器会检查所有主模型的最小运行门禁记录。

### 对比运行

主模型和基线分别生成独立 `run_id`，不得共用同一个结果文件。

### 运行记录结构

`runs/<run_id>/run.json`：

```json
{
  "run_id": "run-001",
  "model_id": "M1",
  "model_role": "primary|baseline",
  "command": "python src/M1/solve.py --config configs/M1.json",
  "status": "succeeded|failed",
  "started_at": "",
  "finished_at": "",
  "random_seed": 42,
  "runtime": {
    "python_version": "",
    "os": "",
    "duration_seconds": 0
  },
  "dependencies": {
    "numpy": "1.24.0",
    "scipy": "1.10.0"
  },
  "parameters": {},
  "reproduce_command": "",
  "input_hashes": {},
  "log_paths": ["runs/run-001/stdout.log", "runs/run-001/stderr.log"],
  "result_paths": ["runs/run-001/results.json"],
  "output_files": [],
  "run_scope": "minimum|full",
  "minimum_gate_passed": true,
  "protocol_path": "validation/plan.json",
  "protocol_hash": "sha256:...",
  "dataset_split_id": "split-001"
}
```

### 输入哈希

记录关键输入文件的哈希，用于门禁失效判断：

```json
{
  "data/raw/data.csv": "sha256:...",
  "configs/M1.json": "sha256:..."
}
```

## 日志要求

- 所有 stdout/stderr 必须保存到日志文件
- 长任务必须持续输出进度
- 日志路径必须登记到 `run.log_paths`

## 结果验证

- 结果文件必须真实存在
- 结果文件必须可解析
- 关键指标必须从结果文件读取，不能依赖控制台输出

## 失败处理

运行失败时：

1. 检查日志定位错误
2. 尝试自动修复（代码、配置、数据）
3. 修复后重试（记录重试次数）
4. 多次失败后尝试备选模型
5. 仍失败时标记为 `failed` 并登记原因

## 进入下一阶段的条件

- 主模型已真实运行并生成结果
- 运行记录、日志和结果文件一致且可读取

## 暂停条件

- 缺少必需的软件、凭据、算力或数据权限
- 预计资源消耗超出限制，需要用户授权
- 多次排错后仍需用户决定精度与成本取舍
