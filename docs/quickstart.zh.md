# 快速上手

本指南带你从全新安装走到一次运行中的研究会话。

## 1. 离线验证安装

在使用 API key 或把 Arbor 指向真实项目之前，先运行内置演示：

```bash
arbor demo
```

它会用真实终端仪表盘、EventBus 和可选 WebUI 回放一次模拟研究运行。它只是信心检查：不调用模型、不修改文件、没有成本。

若要运行一个带领域评估器的示例，可以使用 magnonics 基准：

```bash
arbor demo --benchmark magnonics --no-webui --rounds 1
```

该基准位于 `examples/magnonics_benchmark/`，包含参考色散数据、可编辑候选材料参数、评估脚本、
`outputs/metrics.json`、物理/逻辑可信度检查、证据门控、实验室 intake、人审 gate，以及一个
Arena-lab-inspired 的薄膜自旋动力学场景。该场景明确不是任何实验室、仪器、配方或数据集的精确模型。

你也可以在玩具基准上测试项目初始化：

```bash
cd examples/hello_benchmark
arbor init --run-baseline
```

`arbor init` 会生成 starter `arbor.yaml`，检测 `eval.py` / `eval.sh` 等常见评估脚本，建议受保护路径，并可运行一次基线以确认能看到类似 `score: 0.8123` 的指标。

开始前还可以粗略估算模型预算：

```bash
arbor cost --model claude-sonnet-4-6 --preset standard
arbor cost --model claude-sonnet-4-6 --magnonics-config examples/magnonics_benchmark/configs/example.yaml --preset pilot
```

成本估算适合粗略预算，不是精确账单。真实花费取决于实际轮次、上下文增长、重试、输出长度、缓存命中、provider 路由和当前价格。

## 2. 配置一个 provider

运行一次交互式安装向导。它会把你的 provider、model 和 API key 写入用户配置，这样你就不必每次
运行都重复填写：

```bash
arbor setup
```

!!! tip "首次运行的捷径"
    如果你在配置任何东西之前就启动了一次运行，Arbor 会在交互式终端中检测到缺失的配置，并自动
    引导你走完 `arbor setup`。

更愿意手动来？那就改设环境变量：

=== "Anthropic"

    ```bash
    export ANTHROPIC_API_KEY=sk-ant-...
    ```

=== "OpenAI"

    ```bash
    export OPENAI_API_KEY=sk-...
    ```

=== "OpenAI 兼容（LiteLLM）"

    ```bash
    export OPENAI_API_KEY=...            # 你的网关 key
    export OPENAI_BASE_URL=https://your-gateway/v1
    ```

完整的 provider 矩阵见[配置](configuration.md)。

## 3. 启动一次会话

使用 Arbor 的方式，就是在你的项目目录里运行 `arbor`：

```bash
cd my_project
arbor
```

这会打开一段**接入对话（intake chat）**。你用自然语言描述目标；接入智能体读取你的代码与
README，确认指标与基线，帮你完善出一个计划，待双方达成一致后启动研究。之后你便留在同一个终端中
——观察进度，并用斜杠命令引导运行。

!!! tip "一开始就给出目标"
    你可以把目标作为第一个参数传入，并仍然走接入流程：

    ```bash
    arbor "maximize dev score without changing eval or data"
    ```

??? note "无人值守 / 脚本化运行（CI）"
    若要跳过接入对话——用于基准或 CI——用 `--yes` 跳过聊天，并显式指向项目：

    ```bash
    arbor run "improve held-out accuracy" \
      --yes \
      --yes-cwd /path/to/project \
      --config /path/to/project/research_config.yaml
    ```

    日常使用建议用上面的交互式 `arbor`。

## 4. 观察运行过程

一次运行进行时，你有三个视图：

- **终端仪表盘** —— 当前循环、想法树与成本的实时状态。
- **只读 Web 监控** —— 自动在浏览器中、靠近 `8765` 端口启动（用 `--no-webui` 关闭，用
  `--webui-port` 改端口）。
- **`REPORT.md`** —— 最终成稿，在运行结束时生成。

在仪表盘里你可以用 `/status`、`/tree`、`/evidence`、`/cost`、`/pause`、`/resume` 等斜杠命令
引导运行。见 [CLI 参考](cli.md#interactive-slash-commands)。

## 5. 阅读结果

运行完成后，Arbor 写出一个 `REPORT.md`，并打开一个可选的只读问答提示，让你就这次已完成的
研究进行追问（用 `--no-followup` 关闭）。所有产物——想法树、检查点、日志以及每个实验的分支——都位于
`<project>/.arbor/sessions/<run_name>/` 下。

## 接下来去哪

<div class="grid cards" markdown>

-   :material-book-open-variant: **准备一个基准**

    接好评测命令、保护好数据，让 Arbor 能安全迭代。

    [:octicons-arrow-right-24: 准备基准](preparing-a-benchmark.md)

-   :material-sitemap: **工作原理**

    Arbor 循环、想法树与留出纪律。

    [:octicons-arrow-right-24: 工作原理](how-it-works.md)

</div>
