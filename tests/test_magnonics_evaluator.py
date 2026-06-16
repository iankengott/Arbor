from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = REPO_ROOT / "examples" / "magnonics_benchmark"
EVALUATOR_PATH = BENCHMARK_ROOT / "scripts" / "evaluate.py"


def load_evaluator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("magnonics_evaluator", EVALUATOR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_benchmark(tmp_path: Path) -> Path:
    target = tmp_path / "magnonics_benchmark"
    shutil.copytree(BENCHMARK_ROOT, target, ignore=shutil.ignore_patterns("outputs", "__pycache__"))
    return target


def test_magnonics_evaluator_emits_plausibility_contract(tmp_path: Path) -> None:
    evaluator = load_evaluator()
    benchmark = copy_benchmark(tmp_path)

    result = evaluator.evaluate(benchmark / "configs" / "example.yaml")
    written = json.loads((benchmark / "outputs" / "metrics.json").read_text(encoding="utf-8"))

    assert written == result
    assert result["metric"] == "lab_relevant_magnonics_score"
    assert 0.0 <= result["physics_score"] <= 1.0
    assert 0.0 <= result["plausibility_score"] <= 1.0
    assert 0.0 <= result["dispersion_score"] <= 1.0
    assert 0.0 <= result["objective_components"]["propagation_length"] <= 1.0
    assert result["claim_status"] == "not_promising"
    assert result["can_report_promising"] is False
    assert result["evidence_requirements"]["satisfied"] is True
    assert "dispersion_match" in " ".join(result["evidence_requirements"]["blocked_reasons"])
    assert result["plausibility_failures"] == []
    assert result["material_family"] == "sputtered_re_tm_ferrimagnetic_thin_film"
    assert result["process_route"] == "sputtering"
    assert result["propagation_length_proxy"] > 0.0
    assert result["resonance_frequency"] > 0.0
    assert result["propagation_model"]["linewidth"] > 0.0
    assert result["propagation_model"]["lifetime"] > 0.0
    assert result["propagation_model"]["propagation_length"] == result["propagation_length_proxy"]
    assert result["fmr_constraints"]["field_dependence_monotonic"] is True
    assert result["fmr_constraints"]["linewidth"] == result["propagation_model"]["linewidth"]
    assert result["fmr_constraints"]["anisotropy_field"] > 0.0
    assert result["material_family_schema"]["schema"] == "metallic_ferrimagnetic_alloy"
    assert result["material_family_schema"]["score"] == 1.0
    assert result["temperature_dependence"]["score"] > 0.0
    assert len(result["temperature_dependence"]["temperature_points"]) == 3
    assert result["temperature_dependence"]["temperature_points"][0]["temperature_C"] == 25.0
    assert result["process_constraints"]["score"] == 1.0
    assert result["process_constraints"]["synthesis_difficulty"] == "moderate"
    assert result["process_constraints"]["lab_measurable_observables"] == ["AFM", "hysteresis", "FMR"]
    assert result["literature_search"]["status"] == "supported"
    assert {hit["source"] for hit in result["literature_search"]["hits"]} >= {
        "literature/fe_gd_fmr_sputtered.md",
        "literature/afm_fmr_process_loop.md",
    }
    assert result["material_database"]["status"] == "matched"
    assert result["material_database"]["matches"][0]["material_id"] == "fe_gd_pt_reference"
    assert result["simulator"]["backend"] == "analytic_dispersion"
    assert result["simulator"]["status"] == "completed"
    assert result["demo_scenario"]["status"] == "configured"
    assert result["demo_scenario"]["path"] == "scenario/arena_lab_inspired.yaml"
    assert "Arena-lab-inspired" in result["demo_scenario"]["title"]
    assert "not an exact model" in result["demo_scenario"]["caveat"]
    assert result["demo_scenario"]["spin_dynamics_axes"] == [
        "damping",
        "anisotropy",
        "propagation_length",
        "FMR_linewidth",
        "temperature_dependence",
    ]
    assert result["demo_scenario"]["temperature_axis_C"] == [25.0, 50.0, 100.0]
    assert [stage["stage"] for stage in result["pre_screening_pipeline"]] == [
        "idea",
        "literature_plausibility",
        "database_plausibility",
        "physics_plausibility",
        "simulation_eval",
        "ranked_candidate",
    ]
    assert [item["rank"] for item in result["ranked_candidates"]] == [1, 2, 3, 4]
    assert result["ranked_candidates"][0]["label"] == "dispersion_matched_low_damping_variant"
    assert result["ranked_candidates"][0]["claim_status"] == "promising"
    assert any(item["label"] == "database_fe_gd_pt_reference" for item in result["ranked_candidates"])
    assert result["ranked_candidates"][0]["human_review_status"] == "blocked"
    assert result["ranked_candidates"][0]["can_promote_candidate"] is False
    assert any(item["failure_code"] == "unphysical_damping" for item in result["failure_memory"])
    assert result["lab_intake"]["status"] == "complete"
    assert result["lab_intake"]["target_property"] == "long magnon/spin propagation proxy with low Gilbert damping"
    assert result["lab_intake"]["human_review_required"] is True
    assert result["human_review_gates"]["overall_status"] == "blocked"
    assert result["human_review_gates"]["can_run_deeper_simulation"] is False
    assert result["human_review_gates"]["can_promote_candidate"] is False
    assert [gate["status"] for gate in result["human_review_gates"]["gates"]] == ["pending", "pending"]
    evidence_sources = {item["source"] for item in result["evidence"]}
    assert evidence_sources >= {
        "reference/dispersion.csv",
        "analytic_dispersion_model",
        "AI_README.md#working-lab-specific-defaults",
        "material_family_schema:metallic_ferrimagnetic_alloy",
        "process_constraints:sputtering",
        "materials_database:fe_gd_pt_reference",
        "simulator:analytic_dispersion",
    }
    assert any(source.startswith("literature/") for source in evidence_sources)
    assert {item["type"] for item in result["evidence"]} == {
        "reference_data",
        "evaluator_output",
        "lab_defaults",
        "material_schema",
        "process_window",
        "literature_notes",
        "database_evidence",
        "simulation_output",
    }

    ranked = json.loads((benchmark / "outputs" / "ranked_candidates.json").read_text(encoding="utf-8"))
    failure_memory = json.loads((benchmark / "outputs" / "failure_memory.json").read_text(encoding="utf-8"))
    intake_summary = json.loads((benchmark / "outputs" / "lab_intake_summary.json").read_text(encoding="utf-8"))
    report = (benchmark / "outputs" / "candidate_report.md").read_text(encoding="utf-8")
    assert ranked == result["ranked_candidates"]
    assert failure_memory == result["failure_memory"]
    assert intake_summary == result["lab_intake"]
    assert "Do not trust until measured" in report
    assert "## Executive Summary" in report
    assert "## Ranked Candidates" in report
    assert "## Evaluated Evidence" in report
    assert "## Literature And Database Support" in report
    assert "## Demo Scenario" in report
    assert "Arena-lab-inspired thin-film spin-dynamics screen" in report
    assert "## Model Speculation" in report
    assert "## Physics Checks" in report
    assert "## Research Assistant Checks" in report
    assert "## Human Review Gates" in report
    assert "## Next Lab Measurements" in report


def test_magnonics_evaluator_flags_incomplete_lab_intake(tmp_path: Path) -> None:
    evaluator = load_evaluator()
    benchmark = copy_benchmark(tmp_path)
    (benchmark / "lab_intake.yaml").write_text(
        "\n".join(
            [
                "target_property: low damping",
                "available_instruments: FMR",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = evaluator.evaluate(benchmark / "configs" / "example.yaml")

    assert result["lab_intake"]["status"] == "incomplete"
    assert "materials_of_interest" in result["lab_intake"]["missing_fields"]
    assert "success_criteria" in result["lab_intake"]["missing_fields"]


def test_magnonics_evaluator_flags_implausible_candidate(tmp_path: Path) -> None:
    evaluator = load_evaluator()
    benchmark = copy_benchmark(tmp_path)
    (benchmark / "candidate" / "material_params.yaml").write_text(
        "\n".join(
            [
                "exchange_stiffness: -0.10",
                "anisotropy: -0.20",
                "dmi: 2.50",
                "damping: 0.50",
                "field: -0.10",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = evaluator.evaluate(benchmark / "configs" / "example.yaml")
    failed_rules = {failure["rule"] for failure in result["plausibility_failures"]}

    assert result["physics_score"] < 0.5
    assert result["plausibility_score"] < 0.7
    assert "damping" in failed_rules
    assert "exchange_stiffness" in failed_rules
    assert "anisotropy" in failed_rules
    assert "field" in failed_rules
    assert "dmi" in failed_rules
    assert "stability.exchange_positive" in failed_rules
    assert "stability.non_negative_offsets" in failed_rules


def test_magnonics_evaluator_blocks_promising_claim_without_required_evidence(tmp_path: Path) -> None:
    evaluator = load_evaluator()
    benchmark = copy_benchmark(tmp_path)
    config_path = benchmark / "configs" / "example.yaml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            "required_evidence: evaluator_output,literature_notes,database_evidence",
            "required_evidence: evaluator_output,literature_notes,primary_lab_measurement",
        ),
        encoding="utf-8",
    )

    result = evaluator.evaluate(config_path)

    assert result["evidence_requirements"]["satisfied"] is False
    assert result["evidence_requirements"]["missing_required_evidence"] == ["primary_lab_measurement"]
    assert result["can_report_promising"] is False
    assert result["claim_status"] == "not_promising"


def test_magnonics_evaluator_handles_missing_literature_and_database(tmp_path: Path) -> None:
    evaluator = load_evaluator()
    benchmark = copy_benchmark(tmp_path)
    shutil.rmtree(benchmark / "literature")
    (benchmark / "materials" / "material_systems.csv").unlink()

    result = evaluator.evaluate(benchmark / "configs" / "example.yaml")
    stages = {stage["stage"]: stage["status"] for stage in result["pre_screening_pipeline"]}

    assert result["literature_search"]["status"] == "no_hits"
    assert result["material_database"]["status"] == "no_match"
    assert stages["literature_plausibility"] == "fail"
    assert stages["database_plausibility"] == "fail"
    assert result["evidence_requirements"]["missing_required_evidence"] == [
        "database_evidence",
        "literature_notes",
    ]


def test_magnonics_evaluator_flags_bad_family_process_and_temperature(tmp_path: Path) -> None:
    evaluator = load_evaluator()
    benchmark = copy_benchmark(tmp_path)
    config_path = benchmark / "configs" / "example.yaml"
    config_text = config_path.read_text(encoding="utf-8")
    config_text = config_text.replace(
        "material_family: sputtered_re_tm_ferrimagnetic_thin_film",
        "material_family: garnet",
    )
    config_text = config_text.replace("process_route: sputtering", "process_route: evaporation")
    config_text = config_text.replace("temperature_points_C: 25,50,100", "temperature_points_C: 25,400")
    config_text = config_text.replace("  substrate: Si/SiO2", "  substrate: Copper")
    config_text = config_text.replace("  sputter_pressure_mTorr: 3.0", "  sputter_pressure_mTorr: 50.0")
    config_text = config_text.replace("  anneal_temperature_C: 25.0", "  anneal_temperature_C: 1200.0")
    config_path.write_text(config_text, encoding="utf-8")

    result = evaluator.evaluate(config_path)
    failed_rules = {failure["rule"] for failure in result["plausibility_failures"]}

    assert result["material_family_schema"]["schema"] == "garnet"
    assert result["process_constraints"]["score"] < 1.0
    assert result["temperature_dependence"]["score"] < 1.0
    assert "material_family.damping" in failed_rules
    assert "process.route" in failed_rules
    assert "process.substrate" in failed_rules
    assert "process.sputter_pressure_mTorr" in failed_rules
    assert "process.anneal_temperature_C" in failed_rules
    assert "temperature.window" in failed_rules
