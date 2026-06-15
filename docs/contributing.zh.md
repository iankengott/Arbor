# 贡献

感谢你有兴趣改进 Arbor。本页介绍参与代码库和文档工作的基础。

## 开发环境

```bash
git clone https://github.com/RUC-NLPIR/Arbor.git
cd Arbor
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

验证你的环境：

```bash
arbor doctor
```

## 项目结构

项目使用标准的 `src` 布局。可导入的 Python 包位于 `src/arbor/`：

```text
src/
└── arbor/
    ├── cli/            # Typer CLI：命令、接入对话、仪表盘
    ├── coordinator/    # 研究总监：想法树、编排器、工具
    ├── core/           # 智能体循环、LLM provider、共享工具、配置
    ├── executor/       # 运行单个实验的研究工程师
    ├── events/         # 事件总线 + 订阅者（日志、统计）
    ├── plugins/        # 领域插件（如 mle_kaggle.yaml）
    ├── report/         # REPORT.md 生成
    ├── search_agent/   # 文献/检索智能体
    ├── skills/         # markdown 技能手册
    └── webui/          # 只读浏览器监控
```

!!! note "打包细节"
    `pyproject.toml` 会在 `src/` 下自动发现 setuptools 包，因此新增带
    `__init__.py` 的 `arbor.*` 子包后会自动随 wheel 发布。

## 参与文档

文档站点用 [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) 构建。

```bash
pip install -e ".[docs]"     # 安装文档依赖
mkdocs serve                 # 在 http://127.0.0.1:8000 实时预览
mkdocs build                 # 在 ./site 产出静态站点
```

文档源是 `docs/` 下的 markdown 文件，导航在 `mkdocs.yml` 中定义。要新增一页，创建 markdown 文件
并把它加到 `nav:` 树中。

## 提交改动

1. 为你的改动创建一个分支。
2. 让改动保持聚焦；与周围代码风格一致。
3. 验证 CLI 仍然可用（`arbor version`、`arbor doctor`）；若你动了文档，确认 `mkdocs build`
   无误。
4. 开一个 pull request，说明动机与改动。

## 引用

如果你在研究中使用了 Arbor，请引用论文：

```bibtex
@misc{jin2026arbor,
  title  = {Toward Generalist Autonomous Research via Hypothesis-Tree Refinement},
  author = {Jiajie Jin and Yuyang Hu and Kai Qiu and Qi Dai and Chong Luo and
            Guanting Dong and Xiaoxi Li and Tong Zhao and Xiaolong Ma and
            Gongrui Zhang and Zhirong Wu and Bei Liu and Zhengyuan Yang and
            Linjie Li and Lijuan Wang and Hongjin Qian and Yutao Zhu and Zhicheng Dou},
  year   = {2026},
  eprint = {2606.11926},
  archivePrefix = {arXiv},
  url    = {https://arxiv.org/abs/2606.11926}
}
```
