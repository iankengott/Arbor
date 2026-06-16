# Hello Benchmark

This tiny project is a disposable target for learning Arbor's setup flow. It has
one script that prints a score, so you can test project initialization without
API keys or model calls:

```bash
cd examples/hello_benchmark
arbor init --run-baseline
```

For a real Arbor run, configure a provider first:

```bash
arbor setup
arbor "improve the score without editing eval.py"
```

For the richer magnonics/lab-roadmap demo, see `../magnonics_benchmark/` and
`../../AI_README.md`.
