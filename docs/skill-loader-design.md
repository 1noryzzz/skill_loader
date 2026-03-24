# Incremental Security Skill Loader Design

## Summary
设计一个本地 Python `skill loader + worker`，专门用于代码安全分析，先不考虑 UI。系统默认在每次执行前更新目标仓库，然后基于“自上次成功分析以来的改动模块”做增量分析；只有当用户明确指定“整个代码库”时，才对全仓做轻量发现。Skill 使用本地预编译资产，不在运行时解析原始 `SKILL.md`。默认 skill 为 `security-best-practices`，若用户输入包含 threat-model 相关意图，则切换到 `security-threat-model`。输出先固定为最小可用 JSON。

## Key Changes
### 1. 运行模式与默认行为
- 一等入口为 CLI，内部统一同步函数：`run_analysis(repo_path, user_input=None, scope="auto", output_path=...)`。
- 默认执行流固定为：
  1. 更新仓库：在目标 repo 执行 `git fetch` + fast-forward `pull`，仅支持干净工作树。
  2. 读取本地运行状态：加载上次成功分析记录的 commit SHA。
  3. 计算增量范围：默认比较 `last_successful_commit..HEAD`。
  4. 从改动文件归纳“改动模块”并限定分析范围。
  5. 选择 skill 并装配 prompt。
  6. 调用本地模型。
  7. 解析并落盘 JSON。
  8. 成功后更新本地运行状态。
- 若用户输入显式要求“整个代码库 / 全仓 / full repo / full scan”，跳过增量模块归纳，仅做全仓轻量发现后分析。
- 若没有可用 diff 基线、上次状态缺失、或改动范围过大，则回退到全仓轻量发现，不直接失败。

### 2. Skill 预处理与选择
- 使用两层目录：
  - `skills/raw/`: 原始 skill 来源。
  - `skills/compiled/`: 预处理后的稳定 prompt 资产。
- 编译产物固定包括：
  - `base_system.md`
  - `task_best_practices.md`
  - `task_threat_model.md`
  - `references_index.json`
- 运行时不解析原始 `SKILL.md`；只消费 compiled 资产。
- `skill_selector` 规则固定为：
  - 用户输入包含 `threat model`、`threat modeling`、`abuse path`、`trust boundary` 时选择 `security-threat-model`
  - 其他情况默认 `security-best-practices`
- `security-best-practices` 运行时尝试按 repo 发现结果匹配框架 reference；未命中时回退到 skill 基础规则。
- `security-threat-model` 运行时加载固定模板与控制/资产参考，不做多轮追问，直接输出单轮初版结论。

### 3. Python 组件设计
- `skill_compiler`
  - 从 `skills/raw/` 读取两个 skill，生成 compiled 资产。
  - 仅在 skill 更新后手动或定时运行，不属于每次分析流程。
- `repo_updater`
  - 执行 `git fetch` 和 fast-forward `pull`。
  - 若工作树不干净或无法 fast-forward，则返回明确错误并停止本次分析。
- `run_state_store`
  - 本地保存每个 repo 的上次成功分析信息，至少包含 `repo_id`, `last_commit`, `last_run_at`。
  - 可先用本地 JSON 文件，不引入数据库。
- `diff_scope_builder`
  - 基于 `last_commit..HEAD` 收集改动文件。
  - 将文件按目录/模块聚合，输出 `focus_paths`。
  - 设定一个简单阈值；若改动文件数或模块数超过阈值，则触发全仓轻量发现回退。
- `repo_discovery`
  - 在限定范围或全仓范围内做轻量发现：
    - 语言
    - 框架
    - 入口文件
    - 配置文件
    - 敏感目录
  - 仅依赖文件名规则和 `rg`，不引入 AST。
- `prompt_builder`
  - 固定拼装顺序：
    - 全局系统角色
    - 编译后的 skill system prompt
    - 对应任务模板
    - repo discovery 结果
    - diff/focus_paths
    - 用户输入
    - JSON 输出合同
- `ModelProvider`
  - 抽象接口：`generate(system_prompt, task_prompt, context) -> str`
  - 默认实现：`OllamaHttpProvider`
  - 后续可增补其他本地 provider，不影响上层
- `result_writer`
  - 负责 JSON 校验、落盘、保存原始模型输出备份（仅失败时）

### 4. CLI 接口与 JSON 输出
- CLI 先定义一个主命令即可，例如：
  - `python -m analyzer run --repo /path/to/repo --prompt "audit auth changes" --out result.json`
- CLI 参数最少包含：
  - `--repo`
  - `--prompt` 可选
  - `--scope auto|full`
  - `--out`
  - `--task auto|best_practices|threat_model`
- `--scope` 规则：
  - `auto`: 默认增量分析
  - `full`: 全仓轻量发现
- 最小 JSON schema 固定为：
  - `skill`
  - `task_type`
  - `summary`
  - `findings`
  - `metadata`
- `findings` 字段固定为：
  - `id`
  - `title`
  - `severity`
  - `category`
  - `description`
  - `evidence`
  - `recommendation`
- `metadata` 至少包含：
  - `repo_path`
  - `head_commit`
  - `diff_base`
  - `scope_mode`
  - `focus_paths`
  - `frameworks_detected`
  - `model_name`
  - `partial_context`
- 若模型输出不是合法 JSON，执行一次“JSON 修复重试”；仍失败则返回错误状态并附原始文本路径。

## Test Plan
- 空输入时默认选择 `security-best-practices`
- 输入包含 threat-model 意图时选择 `security-threat-model`
- 默认模式下会先执行仓库更新
- 干净工作树时可完成 fast-forward 更新并进入分析
- 工作树不干净时明确失败，不覆盖用户本地改动
- 存在 `last_successful_commit` 时按该基线计算 diff
- 基线缺失时回退到全仓轻量发现
- 改动文件较少时只分析归纳出的 `focus_paths`
- 用户指定全仓模式时跳过增量模块归纳
- FastAPI/Express/React 仓库能命中正确 reference
- 模型返回合法 JSON 时结果成功落盘
- 模型返回非法 JSON 时触发一次修复重试
- 成功分析后更新本地 run state；失败时不更新基线

## Assumptions
- “更新代码库”固定指 Git fast-forward 更新，不支持任意自定义 shell hook。
- 只支持 Git 仓库，且默认要求分析前工作树干净。
- 增量分析的基线是“上次成功分析的 commit”，不是 `HEAD~1` 或 `origin/main`。
- 若增量上下文不可用或过大，则回退到全仓轻量发现，而不是全仓深度扫描。
- 当前版本只需要成功输出 JSON，不生成 Markdown，不提供 WebUI，不做异步队列。
- 当前版本只做分析，不做自动修复或 PR 生成。
