# Skill Loader

用于本地代码安全分析的 Python `skill loader + worker` 项目。

## 功能概览

- 基于 Git 仓库上下文（提交、变更范围、仓库结构）组装分析提示词。
- 根据用户输入自动选择安全分析 skill。
- 调用 Ollama 模型生成结构化 JSON 结果，并进行 schema 校验与一次修复重试。
- 记录每个仓库最近一次成功分析的提交，用于后续 `auto` 范围分析。

## 目录结构

```text
skill_loader/
  analyzer/          # 核心实现与 CLI
  tests/             # pytest 测试
  docs/              # 设计文档
  pyproject.toml
```

## 环境要求

- Python `>= 3.14`
- Git
- Ollama 服务（默认 `http://localhost:11434`）
- 可用的 Ollama 模型（默认 `llama3`）

## 本地安装与测试

在 `skill_loader` 目录执行：

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install pytest
python -m pytest -q
```

## CLI 用法

查看帮助：

```bash
python -m analyzer --help
python -m analyzer run --help
```

基础运行示例：

```bash
python -m analyzer run \
  --repo /path/to/target-repo \
  --prompt "请对本次改动做安全审查" \
  --out /tmp/security-report.json
```

完整示例：

```bash
python -m analyzer run \
  --repo /path/to/target-repo \
  --prompt "针对认证与权限相关改动做 threat model" \
  --scope auto \
  --out /tmp/security-report.json \
  --model llama3 \
  --ollama-url http://localhost:11434 \
  --state-file .analyzer/run_state.json \
  --skills-root /path/to/skills \
  --max-changed-files 200
```

## 参数说明

- `--repo`: 目标 Git 仓库路径。默认读取环境变量 `ANALYZER_REPO_PATH`，未设置时默认 `.`。
- `--prompt`: 分析任务输入（必填）。
- `--scope`: `auto` 或 `full`。`auto` 会基于上次成功提交做差异范围；`full` 强制全量。
- `--out`: 输出 JSON 文件路径（必填）。
- `--model`: Ollama 模型名，默认 `llama3`。
- `--ollama-url`: Ollama 服务地址，默认 `http://localhost:11434`。
- `--state-file`: 运行状态文件，默认 `.analyzer/run_state.json`。
- `--skills-root`: skills 根目录或 `compiled` 目录路径。默认自动探测。
- `--max-changed-files`: `auto` 模式下允许的最大改动文件数，默认 `200`。

## 路径配置（repo/skills）

为了支持作为独立项目复用，`repo` 与 `skills` 均支持环境变量配置：

```bash
export ANALYZER_REPO_PATH=/path/to/target-repo
export ANALYZER_SKILLS_ROOT=/path/to/skills
```

之后可省略 `--repo` 与 `--skills-root`：

```bash
python -m analyzer run --prompt "安全审查" --out /tmp/report.json
```

`ANALYZER_SKILLS_ROOT` 支持两种目录形态：

- `/path/to/skills`（内部应有 `compiled/*.txt`）
- `/path/to/compiled`

未设置 `ANALYZER_SKILLS_ROOT` 时，默认探测顺序：

1. `当前工作目录/skills`
2. `skill_loader/skills`
3. `skill_loader` 上一级目录的 `skills`

## 输出说明

成功输出为 JSON，顶层包含：

- `skill`
- `task_type`
- `summary`
- `findings`
- `metadata`

当模型输出非法 JSON 时，会自动尝试一次修复；若仍失败，会在输出文件旁生成 `*.raw.txt` 以便排查。

## 运行约束与常见问题

- 仅支持 Git 仓库；若 `--repo` 下无 `.git` 会报错。
- 运行前要求目标仓库工作区干净（无未提交改动）。
- 默认会执行 `git fetch --all --prune` 与 `git pull --ff-only`，请确保网络与远端可用。
- 若找不到 skill 资源，请检查 `--skills-root` 或 `ANALYZER_SKILLS_ROOT` 是否正确指向 `skills` 或 `compiled`。

## 参考文档

- `docs/skill-loader-design.md`
