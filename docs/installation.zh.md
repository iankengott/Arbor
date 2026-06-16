# 安装

## 环境要求

- **Python ≥ 3.10**
- **Git**（Arbor 在隔离的 git worktree 中运行每个实验）
- 至少一个 LLM provider 的 API key（Anthropic、OpenAI，或任何通过 LiteLLM 接入的
  OpenAI 兼容端点）

## 安装

从全新 clone 开始的快速路径：

```bash
git clone https://github.com/RUC-NLPIR/Arbor.git
cd Arbor
./scripts/install.sh
source .venv/bin/activate
arbor demo
```

安装脚本会检查 Python/Git、创建 `.venv`、以可编辑模式安装 Arbor、运行 `arbor doctor`，并打印下一步命令。

手动安装：

```bash
git clone https://github.com/RUC-NLPIR/Arbor.git
cd Arbor
pip install -e .          # 或：uv pip install -e .
```

这一条命令就会把 Arbor 及 `arbor` 命令装进你当前的 Python 环境。我们建议用虚拟环境保持隔离：

=== "venv + pip"

    ```bash
    python -m venv .venv
    source .venv/bin/activate        # Windows：.venv\Scripts\activate
    pip install -e .
    ```

=== "uv"

    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install -e .
    ```

!!! info "为什么用可编辑安装（`-e`）？"
    Arbor 是活跃开发中的研究软件。可编辑安装让你通过 `git pull` 获取更新，而无需重新安装。

## 验证

```bash
arbor version
arbor doctor      # 检查 PATH、venv 泄漏、git 与 API key
arbor demo        # 离线仪表盘/WebUI smoke test；无需 API key
arbor cost --list-models
```

`arbor doctor` 是发现安装问题最快的方式——它会报告你的 shell 解析到哪个 `arbor`、跑在哪个
Python 上、`git` 是否可用，以及用户配置是否存在。如果缺少凭据，安装检查可以通过，但摘要会提示仍需运行 `arbor setup`。

## 可选：用 pipx 安装全局 `arbor` 命令

如果你希望在**任意**目录都能直接用 `arbor` 而无需激活 venv，可用
[pipx](https://pipx.pypa.io) 安装——它会替你管理隔离环境：

```bash
pipx install -e .                 # 在克隆下来的 Arbor 目录中执行
pipx reinstall arbor     # 之后升级
```

## 故障排查

!!! failure "`arbor: command not found`"
    该包被装进了一个未激活、或不在 `PATH` 上的环境。激活正确的虚拟环境，或改用上面的 pipx
    安装。运行 `arbor doctor` 做诊断。

!!! tip "NixOS / shell.nix"
    仓库包含用于开发的 `shell.nix`。如果 console script 被安装到 `PATH` 外，可以用
    `python -m arbor.cli.app ...` 调用同一个 CLI 入口。

## 下一步

- [快速上手](quickstart.md) —— 配置一个 provider 并启动你的第一次运行。
- [配置](configuration.md) —— 每个选项，附示例。
