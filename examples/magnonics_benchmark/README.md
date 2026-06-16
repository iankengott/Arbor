# Magnonics Benchmark

This is a small, self-contained benchmark for trying Arbor on a magnonics-like
optimization task. The target is a synthetic spin-wave dispersion curve. Arbor
may edit `candidate/material_params.yaml`; the evaluator scores a lab-relevant
objective, checks thin-film plausibility using the working lab defaults in
`../../AI_README.md`, gates "promising" claims on supporting evidence, and writes
`outputs/metrics.json`, `outputs/ranked_candidates.json`, and
`outputs/candidate_report.md`.

No external simulator is required. The evaluator uses the Python standard
library so the setup is easy to run anywhere.

This is still a toy benchmark. The included scenario is Arena-lab-inspired and
thin-film spin-dynamics shaped, but it is explicitly not an exact model of any
lab, instrument, recipe, dataset, or unpublished workflow.

```bash
cd examples/magnonics_benchmark
python scripts/evaluate.py --config configs/example.yaml
arbor init --eval-cmd "python scripts/evaluate.py --config configs/example.yaml" --run-baseline
arbor cost --magnonics-config configs/example.yaml --preset pilot
```

For a real run:

```bash
arbor setup
arbor "improve the magnonics score by editing candidate/material_params.yaml only"
```

The primary `score` is `lab_relevant_magnonics_score`, so higher is better. It
rewards propagation-length proxy and low damping while preserving dispersion/FMR
constraints, useful anisotropy, and physical/logical plausibility. The older
curve-fit score remains available as `dispersion_score`.

The metrics also include:

- `physics_score`: bounded checks for damping, exchange, anisotropy, field,
  DMI, group velocity, propagation-length proxy, resonance window, and stability.
- `plausibility_score`: `physics_score` plus material-family and process-route
  feasibility for the sputtered ferrimagnetic thin-film defaults.
- `plausibility_failures`: hard failures or warnings that explain why a
  candidate should not be promoted without revision.
- `propagation_model`: linewidth, lifetime, and propagation length derived from
  group velocity, Gilbert damping, resonance frequency, and inhomogeneous
  linewidth.
- `fmr_constraints`: resonance frequency, linewidth, damping, anisotropy field,
  and field-dependence checks.
- `material_family_schema`: parameter ranges for garnets, ferrites,
  rare-earth iron garnets, metallic ferromagnets/ferrimagnets, antiferromagnets,
  and multilayers.
- `temperature_dependence`: temperature-adjusted damping, anisotropy, lifetime,
  and propagation length.
- `process_constraints`: substrate compatibility, sputter window, anneal window,
  cap-layer expectation, synthesis difficulty, and lab observables.
- `literature_search`: local paper-note search hits with extracted damping,
  anisotropy, propagation ranges, citations, and cautions.
- `material_database`: matches against `materials/material_systems.csv` so
  candidates are tied to known seed systems instead of only invented parameters.
- `simulator`: a stable backend descriptor for analytic, micromagnetic,
  spin-wave, notebook, or external-command evaluators. The bundled backend is
  `analytic_dispersion`.
- `pre_screening_pipeline`: `idea -> literature plausibility -> database
  plausibility -> physics plausibility -> simulation/eval -> ranked candidate`.
- `failure_memory`: domain failure records such as `unphysical_damping`,
  `unsupported_material_family`, `bad_propagation_length`, or `not_lab_feasible`.
- `lab_intake`: parsed `lab_intake.yaml` with target property, instruments,
  materials, forbidden routes, datasets, preferred simulators, and success
  criteria.
- `human_review_gates`: approval gates before deeper simulation or candidate
  promotion.
- `demo_scenario`: the Arena-lab-inspired thin-film scenario, caveat, damping /
  anisotropy / propagation / FMR / temperature axes, and candidate loop.
- `evidence` and `evidence_requirements`: the evaluator/reference/defaults used
  to support scores and decide whether a "promising" claim is allowed.
- `ranked_candidates`: an evaluated shortlist including the editable candidate,
  deterministic next-recipe variants, and a database-grounded candidate when
  available.

The evaluator also writes:

- `outputs/ranked_candidates.json`: ranked candidate summaries with evidence,
  uncertainty, failure modes, and next measurements.
- `outputs/failure_memory.json`: reusable failure codes and reasons for future
  branches.
- `outputs/lab_intake_summary.json`: validated intake fields and warnings.
- `outputs/candidate_report.md`: a human-readable shortlist with a "do not trust
  until measured" caveat, separated evaluated evidence, literature/database
  support, model speculation, review gates, and next measurements.
