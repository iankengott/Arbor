# AI Roadmap

This file is for future AI or human contributors picking up Arbor's onboarding
and magnonics-demo work. It records what exists, what the demo is meant to
prove, and the feature roadmap needed to move from a toy benchmark toward the
research-assistant workflow described in `/home/iank/Desktop/Text File.txt`.

## Current State

Arbor now has several onboarding helpers:

- `arbor demo` runs an offline mock dashboard with no API key.
- `arbor demo --benchmark magnonics` runs the bundled magnonics evaluator before
  the mock dashboard.
- `arbor init` creates a starter `arbor.yaml` and can run a baseline evaluator.
- `arbor cost` estimates rough LLM cost from a preset, custom prices, an
  existing `events.jsonl` file, or a magnonics evaluator config via
  `--magnonics-config`.
- `scripts/install.sh` creates a local virtual environment and installs Arbor.

Environment-key convention for DeepSeek:

- Use `DEEPSEEK_API_KEY` for DeepSeek credentials.
- Do not write the key value into this repository. Reference it as
  `${DEEPSEEK_API_KEY}` in config examples.
- DeepSeek should still be configured as an OpenAI-compatible/LiteLLM endpoint
  with `base_url: https://api.deepseek.com`.

The current magnonics demo lives in `examples/magnonics_benchmark/`.

It includes:

- `candidate/material_params.yaml`: editable toy material parameters.
- `reference/dispersion.csv`: fixed synthetic dispersion data.
- `scripts/evaluate.py`: analytic evaluator.
- `configs/example.yaml`: evaluator config.
- `scenario/arena_lab_inspired.yaml`: Arena-lab-inspired thin-film
  spin-dynamics scenario with an explicit caveat that it is not an exact lab
  model.
- `lab_intake.yaml`: target property, instruments, datasets, simulator
  preferences, success criteria, and human-review defaults.
- `literature/`: tiny local seed note corpus.
- `materials/material_systems.csv`: tiny seed material database.
- `arbor.yaml`: Arbor run config.

The evaluator currently models:

```text
frequency(k) = field + anisotropy + exchange_stiffness * k^2 + dmi * k
```

It scores candidates with a lab-relevant objective that rewards propagation-length
proxy and low damping while preserving dispersion/FMR constraints, useful
anisotropy, and plausibility. It also emits `dispersion_score`,
`physics_score`, `plausibility_score`, `plausibility_failures`,
`propagation_model`, `fmr_constraints`, `material_family_schema`,
`temperature_dependence`, `process_constraints`, `literature_search`,
`material_database`, `simulator`, `pre_screening_pipeline`, `failure_memory`,
`demo_scenario`, `lab_intake`, `human_review_gates`, typed `evidence`, and
evidence-gated claim status using the lab-specific defaults below as
assumptions. It writes `outputs/metrics.json`, `outputs/ranked_candidates.json`,
`outputs/failure_memory.json`, `outputs/lab_intake_summary.json`, and
`outputs/candidate_report.md`.

Important limitation: this is a toy benchmark. It now searches a tiny local
literature-note corpus and seed material database, but it does not yet retrieve
papers from the internet, run real micromagnetic simulation, use a calibrated
materials database, or validate fabrication feasibility. The current
plausibility checker and ranked report are deterministic benchmark guardrails,
not substitutes for simulation, literature review, or lab validation.

## Handoff For Next Session

P0 through P4 are complete for the bundled `examples/magnonics_benchmark/`
demo. Do not restart by re-implementing plausibility scoring, P1 physics checks,
P2 assistant behavior, P3 lab workflow, or P4 polish unless tests show a
regression.

Recommended next work:

1. Replace one toy input with a real source: measured seed data, a real
   simulator backend, a calibrated material table, or internet-backed
   literature retrieval.
2. Keep the existing evidence gates and human-review gates intact while adding
   that source.
3. Preserve the scenario caveat: the Arena-lab-inspired demo is not an exact
   model of any lab, instrument, recipe, dataset, or unpublished workflow.

## Intended Research Workflow

The desired workflow is not "ask an AI for a material and trust it." The goal is
to put a capable general model inside a constrained research framework:

1. Feed it research materials: papers, experimental data, known material
   systems, process constraints, target properties, simulation outputs, and the
   goal.
2. Let it propose hypotheses and candidate materials/processes.
3. Make it verify or falsify ideas using allowed tools: simulators, evaluators,
   materials databases, literature search, and scoring scripts.
4. Record every attempt in the Idea Tree, including failures, rollbacks,
   evidence, and lessons learned.
5. Use a grading/checking layer to ask:
   - Did it cheat by changing the scoring system?
   - Is the result physically/logically plausible?
   - Is it on topic?
   - Is the claim supported by simulation, data, or literature?
   - Is it good enough to pass to a human reviewer?
6. Return a ranked set of candidate directions, not a claimed final truth.

Human review and lab validation remain required.

## Roadmap

## Working Lab-Specific Defaults

Until the lab provides a more precise target, use the following defaults. These
are based on Dr. Arena's lab emphasis on nanomagnetism, thin films,
heterostructures, spin dynamics, FMR, ultrafast/x-ray methods, and publications
on rare-earth/transition-metal ferrimagnetic films, TmIG/Pt magnon propagation,
Fe-Gd anisotropy, and sputtered Pt/Co/Ir multilayers.

1. First property to optimize:
   - Optimize a sputtered ferrimagnetic thin-film stack for long magnon/spin
     propagation proxy and low Gilbert damping while preserving measurable
     magnetic anisotropy and stable magnetic ordering.
   - Primary score should reward low FMR linewidth / low damping and long
     propagation-length proxy.
   - Secondary score should reward useful anisotropy, smooth morphology, and
     process plausibility.

2. Initial material family:
   - Start with sputtered rare-earth/transition-metal ferrimagnetic alloy thin
     films, especially Fe-Gd-like composition/thickness sweeps.
   - Keep Pt/heavy-metal cap or bilayer options available for spin-current /
     spin-Seebeck-style readout.
   - Treat TmIG/Pt and other ferrimagnetic insulator systems as literature
     inspiration, but do not make them the first sputtering demo unless the lab
     confirms the deposition route.

3. Measurement or experiment to model:
   - A thin-film process sweep:
     `composition -> thickness -> sputter pressure/power -> anneal/no anneal -> cap layer`.
   - Characterization proxy:
     AFM roughness, magnetometry/MOKE hysteresis, FMR linewidth-vs-frequency,
     resonance field, effective anisotropy, and optional temperature dependence.
   - The demo should pretend the first useful lab loop is:
     deposit film, check AFM roughness, measure magnetic hysteresis, measure FMR,
     then decide whether the candidate is worth deeper characterization.

4. Assumed tools/data:
   - Local/near-lab tools: sputtering machine, AFM, magnetometry or MOKE,
     FMR/high-frequency magnetic response setup, optical microscope, basic
     thickness/roughness logs, and possibly XRD/XRR if available.
   - Collaboration/user-facility tools: XAS, XRD, x-ray microscopy, PNR, SANS,
     ultrafast optical/XUV/x-ray methods.
   - Demo inputs should include process logs, AFM roughness, magnetic hysteresis
     summary, FMR linewidth table, and a small literature-notes folder.

5. Final output for professor/grad student:
   - A ranked shortlist of candidate film recipes, not a claimed final answer.
   - Each candidate should include composition, thickness, stack/cap,
     sputtering/annealing assumptions, predicted damping, anisotropy,
     propagation proxy, roughness risk, evidence, failure modes, and next lab
     measurement.
   - The report must separate supported evidence from model speculation and
     include a "do not trust until measured" caveat.

### P0: Core Credibility

1. Done: Add a physical/logical plausibility checker.
   - Check realistic bounds for damping, exchange, anisotropy, field, group
     velocity, propagation length, resonance window, stability, and material
     family feasibility.
   - Output both `physics_score` and `plausibility_score`.

2. Done: Add evidence requirements for scientific claims.
   - Arbor should not report a candidate as promising unless it cites evaluator
     output, simulation output, literature notes, or database evidence.

3. Done: Replace the toy target with a lab-relevant objective.
   - Better target: maximize magnon propagation length while matching
     dispersion/FMR constraints and keeping damping, anisotropy, and processing
     assumptions plausible.

4. Done: Generate ranked candidate reports.
   - Include top candidates, why each is plausible, evidence, failed branches,
     uncertainty, suggested experiments, and what humans must verify.

### P1: Magnonics and Physics

5. Done: Add a propagation-length model.
   - Derive propagation length from group velocity and damping/lifetime.

6. Done: Add FMR-style constraints.
   - Include resonance frequency, linewidth, Gilbert damping, anisotropy field,
     and field-dependence checks.

7. Done: Add a material-family schema.
   - Define plausible parameter ranges for garnets, ferrites,
     rare-earth iron garnets, metallic ferromagnets, antiferromagnets, and
     multilayers.

8. Done: Add temperature dependence.
   - Support temperature-dependent damping, anisotropy, and propagation length.

9. Done: Add process/fabrication constraints.
   - Include substrate compatibility, thin-film process assumptions, annealing
     windows, synthesis difficulty, and lab-measurable observables.

### P2: Research Assistant Behavior

10. Done: Add literature-search integration.
    - Retrieve papers, extract material parameters, and attach citations to
      candidate claims.

11. Done: Add materials database/search hooks.
    - Support known material systems instead of invented parameter sets.

12. Done: Add domain-specific failure memory.
    - Record failure reasons like `unphysical_damping`,
      `unsupported_material_family`, `bad_propagation_length`, or
      `not_lab_feasible`.

13. Done: Add simulator/tool abstraction.
    - Let the benchmark call analytic evaluators, micromagnetic solvers,
      spin-wave tools, notebooks, or external packages behind one stable eval
      command.

14. Done: Add a staged pre-screening pipeline.
    - `idea -> literature plausibility -> physics plausibility -> simulation/eval -> ranked candidate`

### P3: Lab Workflow

15. Done: Add a lab intake template.
    - Capture target property, available instruments, materials of interest,
      forbidden materials/processes, available datasets, preferred simulators,
      and success criteria.

16. Done: Add human review gates for scientific claims.
    - Require approval before deeper simulation or before promoting a candidate
      into the final ranked list.

17. Done: Add a mock local literature corpus.
    - Provide small seed notes or paper summaries so the demo can show
      "combining scattered papers" without depending on internet access.

18. Done: Improve final report format.
    - The report should clearly separate measured/evaluated evidence from model
      speculation.

### P4: Polish

19. Tie `arbor cost` to magnonics configs. **Done.**
    - Estimate smoke/pilot/full magnonics runs from the config directly.
    - `arbor cost --magnonics-config examples/magnonics_benchmark/configs/example.yaml --preset smoke|pilot|full`
      now derives run shape from configured FMR points, temperature points,
      local literature notes, material database rows, simulator, evidence, and
      human-review gates.

20. Create an Arena-lab-inspired demo scenario. **Done.**
    - Do not claim to model the lab exactly. Use a thin-film spin-dynamics
      scenario inspired by damping, anisotropy, propagation length, FMR, and
      temperature.
    - `examples/magnonics_benchmark/scenario/arena_lab_inspired.yaml` is loaded
      into evaluator metrics and the candidate report with an explicit caveat
      that it is inspired by public themes, not an exact lab model.

## Suggested Next Implementation Step

P0, P1, P2, P3, and P4 are complete for the bundled magnonics benchmark. The
next useful step is to move beyond the bundled analytic demo: connect a real
simulator or measured seed dataset, then rerun the evidence gates against that
non-toy source.
