from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

LAB_DEFAULTS = {
    "material_family": "sputtered_re_tm_ferrimagnetic_thin_film",
    "process_route": "sputtering",
    "composition": "Fe-Gd-like rare-earth/transition-metal alloy sweep",
    "thickness_nm": 20.0,
    "stack": "substrate / Fe-Gd-like ferrimagnet / Pt cap",
    "cap_layer": "Pt",
    "substrate": "Si/SiO2",
    "sputter_pressure_mTorr": 3.0,
    "sputter_power_W": 75.0,
    "anneal_temperature_C": 25.0,
    "anneal": "no anneal for initial screen",
    "next_measurement": "AFM roughness, MOKE/magnetometry hysteresis, then FMR linewidth-vs-frequency",
}

PROMISING_THRESHOLDS = {
    "score": 0.70,
    "physics_score": 0.70,
    "plausibility_score": 0.70,
    "dispersion_match": 0.60,
    "low_damping": 0.50,
}

ACCEPTED_CLAIM_EVIDENCE = {
    "evaluator_output",
    "simulation_output",
    "literature_notes",
    "database_evidence",
}

OBJECTIVE_WEIGHTS = {
    "propagation_length": 0.30,
    "low_damping": 0.20,
    "dispersion_match": 0.20,
    "fmr_resonance_window": 0.10,
    "useful_anisotropy": 0.10,
    "plausibility": 0.10,
}

PHYSICS_RULES = {
    "damping": {
        "bounds": (0.001, 0.08),
        "ideal": (0.003, 0.03),
        "weight": 1.4,
        "units": "Gilbert damping alpha",
        "message": "Gilbert damping should be positive and low enough for measurable propagation.",
    },
    "exchange_stiffness": {
        "bounds": (0.05, 3.0),
        "ideal": (0.4, 1.6),
        "weight": 1.0,
        "units": "benchmark exchange units",
        "message": "Exchange stiffness should remain positive and in the synthetic thin-film range.",
    },
    "anisotropy": {
        "bounds": (0.02, 1.2),
        "ideal": (0.08, 0.55),
        "weight": 1.0,
        "units": "benchmark anisotropy units",
        "message": "Anisotropy should be measurable without dominating the resonance window.",
    },
    "field": {
        "bounds": (0.02, 1.5),
        "ideal": (0.05, 0.6),
        "weight": 0.8,
        "units": "benchmark field units",
        "message": "Applied field should be non-negative and experimentally accessible.",
    },
    "dmi": {
        "bounds": (-1.0, 1.0),
        "ideal": (-0.25, 0.25),
        "weight": 0.6,
        "units": "benchmark DMI units",
        "message": "DMI should stay within a modest interfacial-coupling range.",
    },
    "group_velocity": {
        "bounds": (0.2, 5.0),
        "ideal": (0.8, 2.8),
        "weight": 1.0,
        "units": "benchmark velocity units",
        "message": "Group velocity should be positive and compatible with the reference dispersion.",
    },
    "propagation_length_proxy": {
        "bounds": (3.0, 300.0),
        "ideal": (10.0, 120.0),
        "weight": 1.2,
        "units": "benchmark length proxy",
        "message": "Propagation proxy should be long enough to matter but not implausibly large.",
    },
    "resonance_frequency": {
        "bounds": (0.05, 5.0),
        "ideal": (0.2, 2.5),
        "weight": 0.8,
        "units": "benchmark frequency units",
        "message": "The k=0 resonance should stay in a measurable synthetic FMR-like window.",
    },
}

MATERIAL_FAMILY_ALIASES = {
    "sputtered_re_tm_ferrimagnetic_thin_film": "metallic_ferrimagnetic_alloy",
    "fe_gd_like_ferrimagnetic_alloy": "metallic_ferrimagnetic_alloy",
    "sputtered_pt_co_ir_multilayer": "multilayer",
    "metallic_ferromagnetic_thin_film": "metallic_ferromagnet",
    "tmig_pt_ferrimagnetic_insulator": "rare_earth_iron_garnet",
    "generic_magnonic_material": "generic_magnonic_material",
}

MATERIAL_FAMILY_SCHEMA = {
    "garnet": {
        "families": ("garnet", "yttrium_iron_garnet"),
        "damping": (0.0001, 0.02),
        "exchange_stiffness": (0.05, 1.5),
        "anisotropy": (0.01, 0.45),
        "field": (0.01, 0.8),
        "dmi": (-0.2, 0.2),
        "process_routes": ("liquid_phase_epitaxy", "pulsed_laser_deposition", "sputtering"),
        "substrates": ("GGG", "YAG", "Si/SiO2"),
        "temperature_C": (-50.0, 250.0),
        "anneal_temperature_C": (500.0, 900.0),
        "lab_priority": 0.6,
    },
    "ferrite": {
        "families": ("ferrite", "spinel_ferrite"),
        "damping": (0.002, 0.08),
        "exchange_stiffness": (0.05, 1.8),
        "anisotropy": (0.02, 1.0),
        "field": (0.01, 1.2),
        "dmi": (-0.3, 0.3),
        "process_routes": ("sputtering", "sol_gel", "pulsed_laser_deposition"),
        "substrates": ("MgO", "Sapphire", "Si/SiO2"),
        "temperature_C": (-50.0, 300.0),
        "anneal_temperature_C": (300.0, 900.0),
        "lab_priority": 0.65,
    },
    "rare_earth_iron_garnet": {
        "families": ("rare_earth_iron_garnet", "tmig_pt_ferrimagnetic_insulator"),
        "damping": (0.0002, 0.035),
        "exchange_stiffness": (0.05, 1.6),
        "anisotropy": (0.02, 0.8),
        "field": (0.01, 1.0),
        "dmi": (-0.3, 0.3),
        "process_routes": ("sputtering", "pulsed_laser_deposition"),
        "substrates": ("GGG", "YAG", "Si/SiO2"),
        "temperature_C": (-100.0, 300.0),
        "anneal_temperature_C": (500.0, 900.0),
        "lab_priority": 0.7,
    },
    "metallic_ferrimagnetic_alloy": {
        "families": ("sputtered_re_tm_ferrimagnetic_thin_film", "fe_gd_like_ferrimagnetic_alloy"),
        "damping": (0.003, 0.08),
        "exchange_stiffness": (0.1, 2.2),
        "anisotropy": (0.02, 1.0),
        "field": (0.02, 1.2),
        "dmi": (-0.8, 0.8),
        "process_routes": ("sputtering", "sputtered_thin_film"),
        "substrates": ("Si/SiO2", "SiN", "Sapphire", "MgO"),
        "temperature_C": (-100.0, 250.0),
        "anneal_temperature_C": (20.0, 350.0),
        "lab_priority": 1.0,
    },
    "metallic_ferromagnet": {
        "families": ("metallic_ferromagnet", "metallic_ferromagnetic_thin_film"),
        "damping": (0.004, 0.12),
        "exchange_stiffness": (0.1, 3.0),
        "anisotropy": (0.01, 1.2),
        "field": (0.02, 1.5),
        "dmi": (-1.0, 1.0),
        "process_routes": ("sputtering", "evaporation"),
        "substrates": ("Si/SiO2", "Sapphire", "MgO"),
        "temperature_C": (-100.0, 250.0),
        "anneal_temperature_C": (20.0, 450.0),
        "lab_priority": 0.8,
    },
    "antiferromagnet": {
        "families": ("antiferromagnet", "synthetic_antiferromagnet"),
        "damping": (0.001, 0.15),
        "exchange_stiffness": (0.1, 3.0),
        "anisotropy": (0.05, 1.5),
        "field": (0.0, 2.0),
        "dmi": (-1.0, 1.0),
        "process_routes": ("sputtering", "molecular_beam_epitaxy"),
        "substrates": ("MgO", "Sapphire", "Si/SiO2"),
        "temperature_C": (-100.0, 300.0),
        "anneal_temperature_C": (20.0, 500.0),
        "lab_priority": 0.55,
    },
    "multilayer": {
        "families": ("multilayer", "sputtered_pt_co_ir_multilayer"),
        "damping": (0.005, 0.15),
        "exchange_stiffness": (0.05, 2.5),
        "anisotropy": (0.05, 1.4),
        "field": (0.02, 1.5),
        "dmi": (-1.5, 1.5),
        "process_routes": ("sputtering", "sputtered_thin_film"),
        "substrates": ("Si/SiO2", "Sapphire", "MgO"),
        "temperature_C": (-50.0, 250.0),
        "anneal_temperature_C": (20.0, 350.0),
        "lab_priority": 0.85,
    },
    "generic_magnonic_material": {
        "families": ("generic_magnonic_material",),
        "damping": (0.001, 0.12),
        "exchange_stiffness": (0.05, 3.0),
        "anisotropy": (0.01, 1.5),
        "field": (0.0, 1.5),
        "dmi": (-1.0, 1.0),
        "process_routes": ("unknown", "sputtering", "thin_film_deposition"),
        "substrates": ("unknown", "Si/SiO2", "Sapphire", "MgO", "GGG"),
        "temperature_C": (-100.0, 300.0),
        "anneal_temperature_C": (20.0, 900.0),
        "lab_priority": 0.35,
    },
}

PROCESS_ROUTE_SCORES = {
    "sputtering": 1.0,
    "sputtered_thin_film": 1.0,
    "thin_film_deposition": 0.8,
    "unknown": 0.35,
}

PROCESS_WINDOWS = {
    "sputtering": {
        "pressure_mTorr": (1.0, 10.0),
        "power_W": (20.0, 200.0),
        "thickness_nm": (2.0, 100.0),
        "requires_cap_for_metallic": True,
    },
    "sputtered_thin_film": {
        "pressure_mTorr": (1.0, 10.0),
        "power_W": (20.0, 200.0),
        "thickness_nm": (2.0, 100.0),
        "requires_cap_for_metallic": True,
    },
    "thin_film_deposition": {
        "pressure_mTorr": (0.1, 20.0),
        "power_W": (5.0, 300.0),
        "thickness_nm": (1.0, 200.0),
        "requires_cap_for_metallic": False,
    },
    "evaporation": {
        "pressure_mTorr": (0.0, 1.0),
        "power_W": (5.0, 150.0),
        "thickness_nm": (1.0, 150.0),
        "requires_cap_for_metallic": True,
    },
    "unknown": {
        "pressure_mTorr": (0.0, 100.0),
        "power_W": (0.0, 500.0),
        "thickness_nm": (0.1, 1000.0),
        "requires_cap_for_metallic": False,
    },
}


def load_simple_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, data)]
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, _, value = line.strip().partition(":")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value.strip() == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(value.strip())
    return data


def parse_scalar(value: str) -> Any:
    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        return value[1:-1]
    try:
        return float(value)
    except ValueError:
        return value


def dispersion(k: float, params: dict[str, float]) -> float:
    exchange = params["exchange_stiffness"]
    anisotropy = params["anisotropy"]
    dmi = params["dmi"]
    field = params["field"]
    return field + anisotropy + exchange * k * k + dmi * k


def load_reference(path: Path) -> list[tuple[float, float]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [(float(row["k"]), float(row["frequency"])) for row in reader]


def finite_difference_group_velocity(params: dict[str, float], k: float = 1.0) -> float:
    h = 1e-3
    return (dispersion(k + h, params) - dispersion(k - h, params)) / (2 * h)


def range_score(value: float, bounds: tuple[float, float], ideal: tuple[float, float]) -> float:
    lower, upper = bounds
    ideal_lower, ideal_upper = ideal
    if value < lower or value > upper:
        return 0.0
    if ideal_lower <= value <= ideal_upper:
        return 1.0
    if value < ideal_lower:
        return (value - lower) / (ideal_lower - lower)
    return (upper - value) / (upper - ideal_upper)


def weighted_average(scores: list[tuple[float, float]]) -> float:
    total_weight = sum(weight for _, weight in scores)
    if total_weight == 0:
        return 0.0
    return sum(score * weight for score, weight in scores) / total_weight


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def benefit_score(value: float, floor: float, target: float) -> float:
    if value <= floor:
        return 0.0
    if value >= target:
        return 1.0
    return (value - floor) / (target - floor)


def lower_is_better_score(value: float, ideal: float, ceiling: float) -> float:
    if value <= ideal:
        return 1.0
    if value >= ceiling:
        return 0.0
    return (ceiling - value) / (ceiling - ideal)


def parse_required_evidence(config: dict[str, Any]) -> set[str]:
    raw = str(config.get("required_evidence", "evaluator_output"))
    return {item.strip() for item in raw.split(",") if item.strip()}


def parse_csv_strings(value: Any) -> tuple[str, ...]:
    return tuple(item.strip() for item in str(value).split(",") if item.strip())


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def normalize_terms(*values: Any) -> set[str]:
    terms: set[str] = set()
    for value in values:
        for chunk in str(value).replace("/", " ").replace("-", " ").replace("_", " ").replace(";", ",").split(","):
            for token in chunk.split():
                cleaned = "".join(char.lower() for char in token if char.isalnum())
                if cleaned and len(cleaned) > 1:
                    terms.add(cleaned)
    return terms


def interval_score(value: float, bounds: tuple[float, float]) -> float:
    return 1.0 if bounds[0] <= value <= bounds[1] else 0.0


def resolve_material_schema(material_family: str) -> tuple[str, dict[str, Any]]:
    schema_name = MATERIAL_FAMILY_ALIASES.get(material_family, material_family)
    schema = MATERIAL_FAMILY_SCHEMA.get(schema_name, MATERIAL_FAMILY_SCHEMA["generic_magnonic_material"])
    return schema_name, schema


def failure(
    rule: str,
    value: Any,
    expected: str,
    message: str,
    severity: str = "error",
) -> dict[str, Any]:
    return {
        "rule": rule,
        "severity": severity,
        "value": value,
        "expected": expected,
        "message": message,
    }


def propagation_length_proxy(group_velocity: float, damping: float, resonance_frequency: float) -> float:
    return propagation_model(group_velocity, damping, resonance_frequency)["propagation_length"]


def propagation_model(
    group_velocity: float,
    damping: float,
    resonance_frequency: float,
    inhomogeneous_linewidth: float = 0.0,
) -> dict[str, float]:
    intrinsic_linewidth = 2.0 * max(damping, 1e-9) * max(resonance_frequency, 1e-9)
    total_linewidth = intrinsic_linewidth + max(inhomogeneous_linewidth, 0.0)
    lifetime = 1.0 / max(total_linewidth, 1e-9)
    return {
        "group_velocity": group_velocity,
        "gilbert_damping": damping,
        "resonance_frequency": resonance_frequency,
        "intrinsic_linewidth": intrinsic_linewidth,
        "inhomogeneous_linewidth": max(inhomogeneous_linewidth, 0.0),
        "linewidth": total_linewidth,
        "lifetime": lifetime,
        "propagation_length": abs(group_velocity) * lifetime,
    }


def fmr_constraints(params: dict[str, float], config: dict[str, Any], group_velocity: float) -> dict[str, Any]:
    resonance_frequency = dispersion(0.0, params)
    anisotropy_field = 2.0 * params.get("anisotropy", 0.0)
    effective_field = params.get("field", 0.0) + anisotropy_field
    linewidth_floor = float(config.get("inhomogeneous_linewidth", 0.0))
    propagation = propagation_model(
        group_velocity=group_velocity,
        damping=params.get("damping", 0.0),
        resonance_frequency=resonance_frequency,
        inhomogeneous_linewidth=linewidth_floor,
    )
    field_points = [
        float(value)
        for value in parse_csv_strings(config.get("fmr_field_points", "0.05,0.18,0.35,0.60"))
    ]
    field_sweep = [
        {
            "field": field,
            "resonance_frequency": dispersion(0.0, {**params, "field": field}),
        }
        for field in field_points
    ]
    monotonic = all(
        later["resonance_frequency"] > earlier["resonance_frequency"]
        for earlier, later in zip(field_sweep, field_sweep[1:])
    )
    linewidth_score = range_score(
        propagation["linewidth"],
        (
            float(config.get("min_linewidth", 0.0001)),
            float(config.get("max_linewidth", 0.20)),
        ),
        (
            float(config.get("ideal_min_linewidth", 0.001)),
            float(config.get("ideal_max_linewidth", 0.08)),
        ),
    )
    resonance_score = range_score(
        resonance_frequency,
        PHYSICS_RULES["resonance_frequency"]["bounds"],
        PHYSICS_RULES["resonance_frequency"]["ideal"],
    )
    anisotropy_field_score = range_score(
        anisotropy_field,
        (
            float(config.get("min_anisotropy_field", 0.04)),
            float(config.get("max_anisotropy_field", 1.60)),
        ),
        (
            float(config.get("ideal_min_anisotropy_field", 0.12)),
            float(config.get("ideal_max_anisotropy_field", 0.90)),
        ),
    )
    damping_score = range_score(
        params.get("damping", 0.0),
        PHYSICS_RULES["damping"]["bounds"],
        PHYSICS_RULES["damping"]["ideal"],
    )
    field_dependence_score = 1.0 if monotonic else 0.0
    score = weighted_average(
        [
            (resonance_score, 1.0),
            (linewidth_score, 1.0),
            (damping_score, 1.0),
            (anisotropy_field_score, 0.8),
            (field_dependence_score, 0.8),
        ]
    )
    failures = []
    if not monotonic:
        failures.append(
            failure(
                rule="fmr.field_dependence",
                value=field_sweep,
                expected="resonance_frequency increases with applied field",
                message="FMR-like field sweep should be monotonic in this benchmark.",
            )
        )
    if linewidth_score == 0.0:
        failures.append(
            failure(
                rule="fmr.linewidth",
                value=propagation["linewidth"],
                expected="configured linewidth window",
                message="FMR linewidth is outside the measurable low-loss window.",
            )
        )
    return {
        "score": score,
        "resonance_frequency": resonance_frequency,
        "linewidth": propagation["linewidth"],
        "intrinsic_linewidth": propagation["intrinsic_linewidth"],
        "gilbert_damping": params.get("damping", 0.0),
        "anisotropy_field": anisotropy_field,
        "effective_field": effective_field,
        "field_dependence_monotonic": monotonic,
        "field_sweep": field_sweep,
        "failures": failures,
    }


def material_family_check(material_family: str, params: dict[str, float]) -> dict[str, Any]:
    schema_name, schema = resolve_material_schema(material_family)
    checks: list[tuple[float, float]] = []
    failures: list[dict[str, Any]] = []
    for param in ("damping", "exchange_stiffness", "anisotropy", "field", "dmi"):
        bounds = schema[param]
        value = params.get(param, 0.0)
        score = interval_score(value, bounds)
        checks.append((score, 1.0))
        if score == 0.0:
            failures.append(
                failure(
                    rule=f"material_family.{param}",
                    value=value,
                    expected=f"{bounds[0]} <= {param} <= {bounds[1]} for {schema_name}",
                    message=f"{param} is outside the {schema_name} material-family range.",
                )
            )
    lab_priority = float(schema["lab_priority"])
    checks.append((lab_priority, 0.6))
    return {
        "schema": schema_name,
        "score": weighted_average(checks),
        "lab_priority": lab_priority,
        "ranges": {
            key: list(schema[key])
            for key in ("damping", "exchange_stiffness", "anisotropy", "field", "dmi", "temperature_C")
        },
        "supported_process_routes": list(schema["process_routes"]),
        "compatible_substrates": list(schema["substrates"]),
        "failures": failures,
    }


def process_constraints(config: dict[str, Any], material_schema: dict[str, Any]) -> dict[str, Any]:
    recipe = recipe_metadata(config)
    process_route = str(config.get("process_route", LAB_DEFAULTS["process_route"]))
    schema_name = material_schema["schema"]
    _, schema = resolve_material_schema(str(config.get("material_family", LAB_DEFAULTS["material_family"])))
    process_window = PROCESS_WINDOWS.get(process_route, PROCESS_WINDOWS["unknown"])
    checks: list[tuple[float, float]] = []
    failures: list[dict[str, Any]] = []

    route_ok = process_route in schema["process_routes"]
    checks.append((1.0 if route_ok else 0.0, 1.0))
    if not route_ok:
        failures.append(
            failure(
                rule="process.route",
                value=process_route,
                expected=", ".join(schema["process_routes"]),
                message=f"{process_route} is not a preferred route for {schema_name}.",
            )
        )

    substrate_ok = recipe["substrate"] in schema["substrates"]
    checks.append((1.0 if substrate_ok else 0.0, 1.0))
    if not substrate_ok:
        failures.append(
            failure(
                rule="process.substrate",
                value=recipe["substrate"],
                expected=", ".join(schema["substrates"]),
                message="Substrate is outside the material-family compatibility list.",
            )
        )

    for key, label in (
        ("thickness_nm", "thickness_nm"),
        ("sputter_pressure_mTorr", "pressure_mTorr"),
        ("sputter_power_W", "power_W"),
    ):
        bounds = process_window[label]
        value = float(recipe[key])
        score = interval_score(value, bounds)
        checks.append((score, 0.8))
        if score == 0.0:
            failures.append(
                failure(
                    rule=f"process.{key}",
                    value=value,
                    expected=f"{bounds[0]} <= {key} <= {bounds[1]}",
                    message=f"{key} is outside the configured thin-film process window.",
                )
            )

    anneal_bounds = schema["anneal_temperature_C"]
    anneal_score = interval_score(float(recipe["anneal_temperature_C"]), anneal_bounds)
    checks.append((anneal_score, 0.6))
    if anneal_score == 0.0:
        failures.append(
            failure(
                rule="process.anneal_temperature_C",
                value=recipe["anneal_temperature_C"],
                expected=f"{anneal_bounds[0]} <= anneal_temperature_C <= {anneal_bounds[1]}",
                message="Anneal assumption is outside the material-family window.",
            )
        )

    cap_required = bool(process_window["requires_cap_for_metallic"]) and schema_name in {
        "metallic_ferrimagnetic_alloy",
        "metallic_ferromagnet",
        "multilayer",
        "antiferromagnet",
    }
    cap_ok = bool(str(recipe["cap_layer"]).strip()) or not cap_required
    checks.append((1.0 if cap_ok else 0.0, 0.6))
    if not cap_ok:
        failures.append(
            failure(
                rule="process.cap_layer",
                value=recipe["cap_layer"],
                expected="cap layer for sputtered metallic stacks",
                message="Metallic sputtered films need a cap/readout layer in this demo.",
            )
        )

    observable_text = str(recipe["next_measurement"])
    required_observables = ("AFM", "hysteresis", "FMR")
    missing_observables = [name for name in required_observables if name.lower() not in observable_text.lower()]
    observables_ok = not missing_observables
    checks.append((1.0 if observables_ok else 0.0, 0.8))
    if missing_observables:
        failures.append(
            failure(
                rule="process.lab_observables",
                value=observable_text,
                expected=", ".join(required_observables),
                message="Next measurements should include roughness, magnetic ordering, and FMR observables.",
                severity="warning",
            )
        )

    return {
        "score": weighted_average(checks),
        "process_route": process_route,
        "substrate": recipe["substrate"],
        "thickness_nm": recipe["thickness_nm"],
        "sputter_pressure_mTorr": recipe["sputter_pressure_mTorr"],
        "sputter_power_W": recipe["sputter_power_W"],
        "anneal_temperature_C": recipe["anneal_temperature_C"],
        "cap_layer": recipe["cap_layer"],
        "synthesis_difficulty": "moderate" if route_ok and substrate_ok else "high",
        "lab_measurable_observables": list(required_observables),
        "failures": failures,
    }


def temperature_dependence(
    params: dict[str, float],
    config: dict[str, Any],
    group_velocity: float,
    material_schema: dict[str, Any],
) -> dict[str, Any]:
    temperatures = [
        float(value)
        for value in parse_csv_strings(config.get("temperature_points_C", "25,50,100"))
    ]
    reference_temperature = float(config.get("temperature_reference_C", 25.0))
    damping_coeff = float(config.get("damping_temp_coefficient", 0.0015))
    anisotropy_coeff = float(config.get("anisotropy_temp_coefficient", 0.0010))
    _, schema = resolve_material_schema(str(config.get("material_family", LAB_DEFAULTS["material_family"])))
    allowed_temp = schema["temperature_C"]
    rows = []
    failures: list[dict[str, Any]] = []
    scores: list[tuple[float, float]] = []
    previous_length: float | None = None
    trend_penalties = 0
    for temperature in temperatures:
        delta = temperature - reference_temperature
        damping_t = max(params.get("damping", 0.0) * (1.0 + damping_coeff * delta), 1e-9)
        anisotropy_t = max(params.get("anisotropy", 0.0) * (1.0 - anisotropy_coeff * delta), 0.0)
        resonance_t = params.get("field", 0.0) + anisotropy_t
        propagation_t = propagation_model(group_velocity, damping_t, resonance_t)
        temp_score = interval_score(temperature, allowed_temp)
        damping_score = range_score(damping_t, PHYSICS_RULES["damping"]["bounds"], PHYSICS_RULES["damping"]["ideal"])
        anisotropy_score = range_score(
            anisotropy_t,
            PHYSICS_RULES["anisotropy"]["bounds"],
            PHYSICS_RULES["anisotropy"]["ideal"],
        )
        scores.append((weighted_average([(temp_score, 1.0), (damping_score, 1.0), (anisotropy_score, 1.0)]), 1.0))
        if temp_score == 0.0:
            failures.append(
                failure(
                    rule="temperature.window",
                    value=temperature,
                    expected=f"{allowed_temp[0]} <= temperature_C <= {allowed_temp[1]} for material family",
                    message="Temperature point is outside the material-family support window.",
                )
            )
        if previous_length is not None and propagation_t["propagation_length"] > previous_length * 1.05:
            trend_penalties += 1
        previous_length = propagation_t["propagation_length"]
        rows.append(
            {
                "temperature_C": temperature,
                "damping": damping_t,
                "anisotropy": anisotropy_t,
                "resonance_frequency": resonance_t,
                "lifetime": propagation_t["lifetime"],
                "propagation_length": propagation_t["propagation_length"],
            }
        )
    trend_score = 1.0 if trend_penalties == 0 else 0.5
    scores.append((trend_score, 0.5))
    if trend_penalties:
        failures.append(
            failure(
                rule="temperature.propagation_trend",
                value=rows,
                expected="propagation length should not improve strongly as damping rises",
                message="Temperature trend is internally suspicious for this simple damping model.",
                severity="warning",
            )
        )
    return {
        "score": weighted_average(scores),
        "reference_temperature_C": reference_temperature,
        "damping_temp_coefficient": damping_coeff,
        "anisotropy_temp_coefficient": anisotropy_coeff,
        "temperature_points": rows,
        "failures": failures,
    }


def parse_key_value_file(path: Path) -> dict[str, Any]:
    metadata: dict[str, Any] = {"path": str(path)}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        key = key.strip()
        value = value.strip()
        if not key or not value:
            continue
        metadata[key] = parse_scalar(value)
    return metadata


def load_literature_notes(root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    literature_dir = root / str(config.get("literature_dir", "literature"))
    if not literature_dir.exists():
        return []
    notes = []
    for path in sorted(literature_dir.glob("*.md")):
        note = parse_key_value_file(path)
        note["source"] = str(path.relative_to(root))
        note["type"] = "literature_notes"
        notes.append(note)
    return notes


def literature_search(
    root: Path | None,
    config: dict[str, Any],
    params: dict[str, float],
    material_family: str,
    process_route: str,
    recipe: dict[str, Any],
    propagation_length: float,
) -> dict[str, Any]:
    if root is None:
        return {"query": [], "hits": [], "score": 0.0, "status": "not_configured"}
    notes = load_literature_notes(root, config)
    query_terms = normalize_terms(
        config.get("literature_query", ""),
        material_family,
        process_route,
        recipe["composition"],
        recipe["cap_layer"],
        "damping anisotropy FMR propagation",
    )
    hits = []
    for note in notes:
        note_terms = normalize_terms(
            note.get("title", ""),
            note.get("material_family", ""),
            note.get("materials", ""),
            note.get("process_routes", ""),
            note.get("keywords", ""),
            note.get("supports", ""),
        )
        overlap = sorted(query_terms & note_terms)
        family_match = str(note.get("material_family", "")) == material_family
        route_match = process_route in parse_csv_strings(note.get("process_routes", ""))
        damping_match = float(note.get("damping_min", -math.inf)) <= params.get("damping", 0.0) <= float(
            note.get("damping_max", math.inf)
        )
        anisotropy_match = float(note.get("anisotropy_min", -math.inf)) <= params.get("anisotropy", 0.0) <= float(
            note.get("anisotropy_max", math.inf)
        )
        propagation_match = float(note.get("propagation_length_min", -math.inf)) <= propagation_length <= float(
            note.get("propagation_length_max", math.inf)
        )
        score = weighted_average(
            [
                (min(len(overlap) / 5.0, 1.0), 1.0),
                (1.0 if family_match else 0.0, 1.2),
                (1.0 if route_match else 0.0, 0.8),
                (1.0 if damping_match else 0.0, 0.8),
                (1.0 if anisotropy_match else 0.0, 0.6),
                (1.0 if propagation_match else 0.0, 0.6),
            ]
        )
        if score > 0.25:
            hits.append(
                {
                    "source": note["source"],
                    "title": note.get("title", ""),
                    "citation": note.get("citation", ""),
                    "score": score,
                    "matched_terms": overlap,
                    "extracted_parameters": {
                        "damping": [float(note.get("damping_min", 0.0)), float(note.get("damping_max", 0.0))],
                        "anisotropy": [
                            float(note.get("anisotropy_min", 0.0)),
                            float(note.get("anisotropy_max", 0.0)),
                        ],
                        "propagation_length": [
                            float(note.get("propagation_length_min", 0.0)),
                            float(note.get("propagation_length_max", 0.0)),
                        ],
                    },
                    "supports": note.get("supports", ""),
                    "cautions": note.get("cautions", ""),
                }
            )
    hits.sort(key=lambda item: item["score"], reverse=True)
    return {
        "query": sorted(query_terms),
        "hits": hits[:3],
        "score": hits[0]["score"] if hits else 0.0,
        "status": "supported" if hits else "no_hits",
    }


def load_material_database(root: Path, config: dict[str, Any]) -> list[dict[str, str]]:
    database_path = root / str(config.get("materials_database", "materials/material_systems.csv"))
    if not database_path.exists():
        return []
    with database_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


LAB_INTAKE_REQUIRED_FIELDS = (
    "target_property",
    "available_instruments",
    "materials_of_interest",
    "forbidden_materials",
    "forbidden_processes",
    "available_datasets",
    "preferred_simulators",
    "success_criteria",
)


def lab_intake(root: Path | None, config: dict[str, Any]) -> dict[str, Any]:
    if root is None:
        return {"status": "not_configured", "path": None, "missing_fields": list(LAB_INTAKE_REQUIRED_FIELDS)}
    path = root / str(config.get("lab_intake", "lab_intake.yaml"))
    if not path.exists():
        return {"status": "missing", "path": str(path), "missing_fields": list(LAB_INTAKE_REQUIRED_FIELDS)}
    data = load_simple_yaml(path)
    missing = [field for field in LAB_INTAKE_REQUIRED_FIELDS if not str(data.get(field, "")).strip()]
    instruments = parse_csv_strings(data.get("available_instruments", ""))
    datasets = parse_csv_strings(data.get("available_datasets", ""))
    preferred_simulators = parse_csv_strings(data.get("preferred_simulators", ""))
    forbidden_processes = parse_csv_strings(data.get("forbidden_processes", ""))
    simulator = simulator_config(config)
    route = str(config.get("process_route", ""))
    warnings = []
    if route in forbidden_processes:
        warnings.append(f"Configured process_route {route} is forbidden by intake.")
    if simulator["backend"] not in preferred_simulators:
        warnings.append(f"Simulator backend {simulator['backend']} is not listed in preferred_simulators.")
    for dataset in datasets:
        if "*" in dataset:
            if not list(root.glob(dataset)):
                warnings.append(f"Dataset pattern {dataset} did not match any files.")
        elif not (root / dataset).exists():
            warnings.append(f"Dataset {dataset} is listed but missing.")
    return {
        "status": "complete" if not missing else "incomplete",
        "path": str(path.relative_to(root)),
        "missing_fields": missing,
        "warnings": warnings,
        "target_property": data.get("target_property", ""),
        "available_instruments": list(instruments),
        "materials_of_interest": list(parse_csv_strings(data.get("materials_of_interest", ""))),
        "forbidden_materials": list(parse_csv_strings(data.get("forbidden_materials", ""))),
        "forbidden_processes": list(forbidden_processes),
        "available_datasets": list(datasets),
        "preferred_simulators": list(preferred_simulators),
        "success_criteria": list(parse_csv_strings(data.get("success_criteria", ""))),
        "human_review_required": parse_bool(data.get("human_review_required", True)),
        "review_before_deeper_simulation": parse_bool(data.get("review_before_deeper_simulation", True)),
        "review_before_promoting_candidate": parse_bool(data.get("review_before_promoting_candidate", True)),
        "do_not_trust_until_measured": parse_bool(data.get("do_not_trust_until_measured", True)),
    }


def demo_scenario(root: Path | None, config: dict[str, Any]) -> dict[str, Any]:
    scenario_path = config.get("demo_scenario") or config.get("scenario")
    if root is None or not scenario_path:
        return {
            "status": "not_configured",
            "path": "",
            "title": "",
            "caveat": "No demo scenario was configured.",
            "spin_dynamics_axes": [],
            "temperature_axis_C": [],
        }

    path = root / str(scenario_path)
    if not path.exists():
        return {
            "status": "missing",
            "path": str(path.relative_to(root)),
            "title": "",
            "caveat": "Configured demo scenario file is missing.",
            "spin_dynamics_axes": [],
            "temperature_axis_C": [],
        }

    data = load_simple_yaml(path)
    caveat = str(
        data.get(
            "caveat",
            "Inspired by thin-film spin-dynamics themes; not an exact model of any lab, instrument, recipe, or dataset.",
        )
    )
    return {
        "status": "configured",
        "path": str(path.relative_to(root)),
        "title": str(data.get("title", "Thin-film spin-dynamics demo scenario")),
        "caveat": caveat,
        "material_system": str(data.get("material_system", "")),
        "spin_dynamics_axes": list(parse_csv_strings(data.get("spin_dynamics_axes", ""))),
        "temperature_axis_C": [float(item) for item in parse_csv_strings(data.get("temperature_axis_C", ""))],
        "candidate_loop": list(parse_csv_strings(data.get("candidate_loop", ""))),
        "primary_success_signal": str(data.get("primary_success_signal", "")),
        "failure_modes": list(parse_csv_strings(data.get("failure_modes", ""))),
        "forbidden_claim": str(data.get("forbidden_claim", "")),
        "human_review_focus": str(data.get("human_review_focus", "")),
    }


def material_database_search(
    root: Path | None,
    config: dict[str, Any],
    params: dict[str, float],
    material_family: str,
    process_route: str,
    recipe: dict[str, Any],
    propagation_length: float,
) -> dict[str, Any]:
    if root is None:
        return {"matches": [], "score": 0.0, "status": "not_configured"}
    rows = load_material_database(root, config)
    matches = []
    for row in rows:
        process_routes = {item.strip() for item in row.get("process_routes", "").split(";") if item.strip()}
        substrates = {item.strip() for item in row.get("substrates", "").split(";") if item.strip()}
        caps = {item.strip() for item in row.get("cap_layers", "").split(";") if item.strip()}
        checks = [
            (1.0 if row.get("material_family") == material_family else 0.0, 1.4),
            (1.0 if process_route in process_routes else 0.0, 1.0),
            (1.0 if recipe["substrate"] in substrates else 0.0, 0.8),
            (1.0 if recipe["cap_layer"] in caps else 0.0, 0.6),
            (
                1.0
                if float(row["damping_min"]) <= params.get("damping", 0.0) <= float(row["damping_max"])
                else 0.0,
                1.0,
            ),
            (
                1.0
                if float(row["anisotropy_min"]) <= params.get("anisotropy", 0.0) <= float(row["anisotropy_max"])
                else 0.0,
                0.8,
            ),
            (
                1.0
                if float(row["exchange_min"]) <= params.get("exchange_stiffness", 0.0) <= float(row["exchange_max"])
                else 0.0,
                0.7,
            ),
            (
                1.0 if float(row["dmi_min"]) <= params.get("dmi", 0.0) <= float(row["dmi_max"]) else 0.0,
                0.5,
            ),
            (
                1.0
                if float(row["propagation_min"]) <= propagation_length <= float(row["propagation_max"])
                else 0.0,
                0.7,
            ),
        ]
        score = weighted_average(checks)
        if score > 0.25:
            matches.append(
                {
                    "material_id": row["material_id"],
                    "name": row["name"],
                    "score": score,
                    "material_family": row["material_family"],
                    "notes": row.get("notes", ""),
                    "parameter_ranges": {
                        "damping": [float(row["damping_min"]), float(row["damping_max"])],
                        "anisotropy": [float(row["anisotropy_min"]), float(row["anisotropy_max"])],
                        "exchange_stiffness": [float(row["exchange_min"]), float(row["exchange_max"])],
                        "dmi": [float(row["dmi_min"]), float(row["dmi_max"])],
                        "propagation_length": [float(row["propagation_min"]), float(row["propagation_max"])],
                    },
                }
            )
    matches.sort(key=lambda item: item["score"], reverse=True)
    return {
        "matches": matches[:3],
        "score": matches[0]["score"] if matches else 0.0,
        "status": "matched" if matches else "no_match",
    }


def simulator_config(config: dict[str, Any]) -> dict[str, Any]:
    configured = config.get("simulator", {})
    if not isinstance(configured, dict):
        configured = {}
    backend = str(configured.get("backend", "analytic_dispersion"))
    return {
        "backend": backend,
        "kind": str(configured.get("kind", "analytic")),
        "command": str(configured.get("command", "python scripts/evaluate.py --config configs/example.yaml")),
        "status": str(configured.get("status", "available" if backend == "analytic_dispersion" else "configured")),
        "supported_backends": [
            "analytic_dispersion",
            "micromagnetic_solver",
            "spin_wave_tool",
            "notebook",
            "external_command",
        ],
    }


def human_review_gates(config: dict[str, Any], intake: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    configured = config.get("human_review", {})
    if not isinstance(configured, dict):
        configured = {}
    review_required = bool(intake.get("human_review_required", True))
    before_deeper = parse_bool(configured.get("require_before_deeper_simulation", intake.get("review_before_deeper_simulation", True)))
    before_promoting = parse_bool(configured.get("require_before_promoting_candidate", intake.get("review_before_promoting_candidate", True)))
    reviewer = str(configured.get("reviewer", "human reviewer"))
    status = str(configured.get("status", "pending"))
    gates = [
        {
            "gate": "before_deeper_simulation",
            "required": review_required and before_deeper,
            "status": status if review_required and before_deeper else "not_required",
            "reason": "Human approval required before running deeper non-analytic simulation.",
        },
        {
            "gate": "before_promoting_candidate",
            "required": review_required and before_promoting,
            "status": status if review_required and before_promoting else "not_required",
            "reason": "Human approval required before promoting a candidate into the final shortlist.",
        },
    ]
    approval_ready = candidate.get("claim_status") == "promising" and all(
        gate["status"] == "approved" or not gate["required"] for gate in gates
    )
    return {
        "reviewer": reviewer,
        "overall_status": "approved" if approval_ready else "blocked",
        "can_run_deeper_simulation": not gates[0]["required"] or gates[0]["status"] == "approved",
        "can_promote_candidate": approval_ready,
        "gates": gates,
        "instructions": [
            "Review supported evidence separately from model speculation.",
            "Approve deeper simulation only after checking target, instruments, and forbidden processes.",
            "Approve promotion only after evidence, plausibility, and measurement caveats are acceptable.",
        ],
    }


def run_simulator_backend(
    config: dict[str, Any],
    params: dict[str, float],
    reference: list[tuple[float, float]],
) -> dict[str, Any]:
    sim = simulator_config(config)
    predictions = [(k, dispersion(k, params)) for k, _ in reference]
    mse = sum((pred - target) ** 2 for (_, pred), (_, target) in zip(predictions, reference)) / len(reference)
    if sim["backend"] == "analytic_dispersion":
        return {
            **sim,
            "ran": True,
            "status": "completed",
            "rmse": math.sqrt(mse),
            "outputs": ["outputs/metrics.json", "outputs/predicted_dispersion.csv"],
        }
    return {
        **sim,
        "ran": False,
        "status": "not_available",
        "rmse": math.sqrt(mse),
        "outputs": [],
        "message": "Non-analytic simulator backend is registered but not available in this offline benchmark.",
    }


FAILURE_CODE_RULES = (
    ("unphysical_damping", ("damping", "linewidth")),
    ("unsupported_material_family", ("material_family",)),
    ("bad_propagation_length", ("propagation",)),
    ("not_lab_feasible", ("process", "substrate", "anneal", "cap_layer", "temperature")),
    ("unsupported_evidence", ("evidence", "literature", "database")),
    ("unstable_dispersion", ("stability", "exchange", "anisotropy", "field")),
)


def classify_failure_memory(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    raw_reasons = [failure["rule"] for failure in candidate.get("plausibility_failures", [])]
    raw_reasons.extend(candidate.get("evidence_requirements", {}).get("blocked_reasons", []))
    raw_reasons.extend(
        stage["reason"]
        for stage in candidate.get("pre_screening_pipeline", [])
        if stage.get("status") in {"fail", "warn"}
    )
    for reason in raw_reasons:
        reason_text = str(reason)
        code = "needs_review"
        for candidate_code, terms in FAILURE_CODE_RULES:
            if any(term in reason_text.lower() for term in terms):
                code = candidate_code
                break
        records.append(
            {
                "candidate": candidate["label"],
                "failure_code": code,
                "reason": reason_text,
                "score": candidate["score"],
            }
        )
    return records


def build_pre_screening_pipeline(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    literature = candidate["literature_search"]
    database = candidate["material_database"]
    simulator = candidate["simulator"]
    return [
        {
            "stage": "idea",
            "status": "pass",
            "reason": f"Candidate recipe loaded from {candidate['origin']}.",
        },
        {
            "stage": "literature_plausibility",
            "status": "pass" if literature["hits"] else "fail",
            "reason": f"{len(literature['hits'])} literature hit(s) found.",
        },
        {
            "stage": "database_plausibility",
            "status": "pass" if database["matches"] else "fail",
            "reason": f"{len(database['matches'])} material database match(es) found.",
        },
        {
            "stage": "physics_plausibility",
            "status": "pass" if candidate["physics_score"] >= PROMISING_THRESHOLDS["physics_score"] else "fail",
            "reason": f"physics_score={candidate['physics_score']:.3f}.",
        },
        {
            "stage": "simulation_eval",
            "status": "pass" if simulator["status"] == "completed" else "warn",
            "reason": f"{simulator['backend']} status={simulator['status']}.",
        },
        {
            "stage": "ranked_candidate",
            "status": "pass" if candidate["claim_status"] == "promising" else "warn",
            "reason": f"claim_status={candidate['claim_status']}, score={candidate['score']:.3f}.",
        },
    ]


def objective_weights(config: dict[str, Any]) -> dict[str, float]:
    configured = config.get("objective_weights", {})
    if not isinstance(configured, dict):
        configured = {}
    return {name: float(configured.get(name, weight)) for name, weight in OBJECTIVE_WEIGHTS.items()}


def lab_objective_components(
    params: dict[str, float],
    config: dict[str, Any],
    rmse: float,
    velocity_error: float,
    plausibility: dict[str, Any],
) -> dict[str, Any]:
    target_length = float(config.get("target_propagation_length", 35.0))
    minimum_length = float(config.get("minimum_propagation_length", 8.0))
    max_damping = float(config.get("max_preferred_damping", 0.06))
    target_damping = float(config.get("target_damping", 0.025))
    dispersion_score = 1.0 / (1.0 + rmse)
    velocity_constraint_score = 1.0 / (1.0 + velocity_error)
    resonance_score = range_score(
        float(plausibility["resonance_frequency"]),
        PHYSICS_RULES["resonance_frequency"]["bounds"],
        PHYSICS_RULES["resonance_frequency"]["ideal"],
    )
    components = {
        "propagation_length": benefit_score(
            float(plausibility["propagation_length_proxy"]),
            floor=minimum_length,
            target=target_length,
        ),
        "low_damping": lower_is_better_score(params.get("damping", 0.0), ideal=target_damping, ceiling=max_damping),
        "dispersion_match": dispersion_score,
        "fmr_resonance_window": weighted_average([(resonance_score, 0.7), (velocity_constraint_score, 0.3)]),
        "useful_anisotropy": range_score(
            params.get("anisotropy", 0.0),
            PHYSICS_RULES["anisotropy"]["bounds"],
            PHYSICS_RULES["anisotropy"]["ideal"],
        ),
        "plausibility": float(plausibility["plausibility_score"]),
    }
    weights = objective_weights(config)
    score = weighted_average([(components[name], weights[name]) for name in OBJECTIVE_WEIGHTS])
    return {
        "score": score,
        "weights": weights,
        "components": components,
        "targets": {
            "target_propagation_length": target_length,
            "minimum_propagation_length": minimum_length,
            "target_damping": target_damping,
            "max_preferred_damping": max_damping,
        },
    }


def assess_claim_support(
    evidence: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    lab_score: float,
    physics_score: float,
    plausibility_score: float,
    objective_components: dict[str, float],
    config: dict[str, Any],
) -> dict[str, Any]:
    present_types = {str(item.get("type", "")) for item in evidence}
    required = parse_required_evidence(config)
    accepted_present = sorted(present_types & ACCEPTED_CLAIM_EVIDENCE)
    missing_required = sorted(required - present_types)
    hard_failures = [item for item in failures if item.get("severity") == "error"]
    threshold_failures = []
    if lab_score < PROMISING_THRESHOLDS["score"]:
        threshold_failures.append(
            f"score {lab_score:.3f} < required {PROMISING_THRESHOLDS['score']:.3f}"
        )
    if physics_score < PROMISING_THRESHOLDS["physics_score"]:
        threshold_failures.append(
            f"physics_score {physics_score:.3f} < required {PROMISING_THRESHOLDS['physics_score']:.3f}"
        )
    if plausibility_score < PROMISING_THRESHOLDS["plausibility_score"]:
        threshold_failures.append(
            "plausibility_score "
            f"{plausibility_score:.3f} < required {PROMISING_THRESHOLDS['plausibility_score']:.3f}"
        )
    for component in ("dispersion_match", "low_damping"):
        if objective_components.get(component, 0.0) < PROMISING_THRESHOLDS[component]:
            threshold_failures.append(
                f"{component} {objective_components.get(component, 0.0):.3f} "
                f"< required {PROMISING_THRESHOLDS[component]:.3f}"
            )

    evidence_satisfied = bool(accepted_present) and not missing_required
    can_report_promising = evidence_satisfied and not hard_failures and not threshold_failures
    blocked_reasons = []
    if not accepted_present:
        blocked_reasons.append(
            "No evaluator, simulation, literature, or database evidence is attached to the candidate claim."
        )
    if missing_required:
        blocked_reasons.append(f"Missing required evidence type(s): {', '.join(missing_required)}.")
    if hard_failures:
        blocked_reasons.append(
            "Hard plausibility failure(s): "
            + ", ".join(str(item.get("rule")) for item in hard_failures)
            + "."
        )
    blocked_reasons.extend(threshold_failures)

    return {
        "accepted_evidence_types": sorted(ACCEPTED_CLAIM_EVIDENCE),
        "present_evidence_types": sorted(item for item in present_types if item),
        "required_evidence_types": sorted(required),
        "missing_required_evidence": missing_required,
        "satisfied": evidence_satisfied,
        "can_report_promising": can_report_promising,
        "claim_status": "promising" if can_report_promising else "not_promising",
        "blocked_reasons": blocked_reasons,
        "thresholds": PROMISING_THRESHOLDS,
    }


def plausibility_checks(
    params: dict[str, float],
    config: dict[str, Any],
    reference_count: int,
    rmse: float,
    group_velocity: float,
) -> dict[str, Any]:
    material_family = str(config.get("material_family", LAB_DEFAULTS["material_family"]))
    process_route = str(config.get("process_route", LAB_DEFAULTS["process_route"]))
    resonance_frequency = dispersion(0.0, params)
    linewidth_floor = float(config.get("inhomogeneous_linewidth", 0.0))
    propagation = propagation_model(
        group_velocity=group_velocity,
        damping=params.get("damping", 0.0),
        resonance_frequency=resonance_frequency,
        inhomogeneous_linewidth=linewidth_floor,
    )
    length_proxy = propagation["propagation_length"]
    fmr = fmr_constraints(params, config, group_velocity)
    material_schema = material_family_check(material_family, params)
    process = process_constraints(config, material_schema)
    temperature = temperature_dependence(params, config, group_velocity, material_schema)
    checked_values = {
        "damping": params.get("damping", 0.0),
        "exchange_stiffness": params.get("exchange_stiffness", 0.0),
        "anisotropy": params.get("anisotropy", 0.0),
        "field": params.get("field", 0.0),
        "dmi": params.get("dmi", 0.0),
        "group_velocity": group_velocity,
        "propagation_length_proxy": length_proxy,
        "resonance_frequency": resonance_frequency,
    }

    failures: list[dict[str, Any]] = []
    physics_parts: list[tuple[float, float]] = []
    for name, rule in PHYSICS_RULES.items():
        value = checked_values[name]
        bounds = rule["bounds"]
        ideal = rule["ideal"]
        score = range_score(value, bounds, ideal)
        physics_parts.append((score, float(rule["weight"])))
        if score == 0.0:
            failures.append(
                failure(
                    rule=name,
                    value=value,
                    expected=f"{bounds[0]} <= value <= {bounds[1]} {rule['units']}",
                    message=str(rule["message"]),
                )
            )

    stability_score = 1.0
    if params.get("exchange_stiffness", 0.0) <= 0:
        stability_score = 0.0
        failures.append(
            failure(
                rule="stability.exchange_positive",
                value=params.get("exchange_stiffness", 0.0),
                expected="exchange_stiffness > 0",
                message="Negative exchange makes the dispersion logically unstable.",
            )
        )
    if params.get("anisotropy", 0.0) < 0 or params.get("field", 0.0) < 0:
        stability_score = 0.0
        failures.append(
            failure(
                rule="stability.non_negative_offsets",
                value={"anisotropy": params.get("anisotropy", 0.0), "field": params.get("field", 0.0)},
                expected="anisotropy >= 0 and field >= 0",
                message="Negative anisotropy or field breaks this benchmark's FMR-like offset assumptions.",
            )
        )
    physics_parts.append((stability_score, 1.2))
    physics_parts.append((fmr["score"], 1.0))
    physics_parts.append((temperature["score"], 0.8))
    physics_score = weighted_average(physics_parts)

    schema_name = material_schema["schema"]
    family_score = material_schema["score"]
    if schema_name == "generic_magnonic_material":
        failures.append(
            failure(
                rule="material_family.lab_priority",
                value=material_family,
                expected=LAB_DEFAULTS["material_family"],
                message="Material family is generic or not the preferred first sputtering demo.",
                severity="warning",
            )
        )
    failures.extend(material_schema["failures"])
    failures.extend(fmr["failures"])
    failures.extend(process["failures"])
    failures.extend(temperature["failures"])

    process_score = PROCESS_ROUTE_SCORES.get(process_route, 0.0) * process["score"]
    if process_score == 0.0:
        failures.append(
            failure(
                rule="process_route.feasibility",
                value=process_route,
                expected=", ".join(sorted(PROCESS_ROUTE_SCORES)),
                message="Process route is not supported by the lab-default tool assumptions.",
            )
        )

    plausibility_score = weighted_average(
        [
            (physics_score, 4.0),
            (family_score, 1.4),
            (process_score, 1.2),
            (fmr["score"], 1.0),
            (temperature["score"], 0.8),
        ]
    )
    evidence = [
        {
            "type": "reference_data",
            "source": "reference/dispersion.csv",
            "supports": "RMSE was computed against held-out synthetic dispersion points.",
            "reference_points": reference_count,
            "rmse": rmse,
        },
        {
            "type": "evaluator_output",
            "source": "analytic_dispersion_model",
            "supports": "Dispersion, group velocity, resonance window, and propagation proxy were computed deterministically.",
            "model": "frequency(k) = field + anisotropy + exchange_stiffness * k^2 + dmi * k",
            "group_velocity": group_velocity,
            "resonance_frequency": resonance_frequency,
            "linewidth": propagation["linewidth"],
            "lifetime": propagation["lifetime"],
            "propagation_length_proxy": length_proxy,
        },
        {
            "type": "lab_defaults",
            "source": "AI_README.md#working-lab-specific-defaults",
            "supports": "Plausibility bounds use the sputtered ferrimagnetic thin-film defaults from the roadmap.",
            "material_family": material_family,
            "process_route": process_route,
        },
        {
            "type": "material_schema",
            "source": f"material_family_schema:{schema_name}",
            "supports": "Material-family parameter, substrate, process, and temperature ranges were checked.",
            "schema": schema_name,
            "score": family_score,
        },
        {
            "type": "process_window",
            "source": f"process_constraints:{process_route}",
            "supports": "Thin-film process assumptions were checked against configured fabrication windows.",
            "score": process["score"],
        },
    ]
    return {
        "physics_score": physics_score,
        "plausibility_score": plausibility_score,
        "plausibility_failures": failures,
        "evidence": evidence,
        "propagation_model": propagation,
        "propagation_length_proxy": length_proxy,
        "resonance_frequency": resonance_frequency,
        "fmr_constraints": fmr,
        "material_family_schema": material_schema,
        "process_constraints": process,
        "temperature_dependence": temperature,
        "material_family": material_family,
        "process_route": process_route,
    }


def score_material_candidate(
    label: str,
    origin: str,
    params: dict[str, float],
    config: dict[str, Any],
    reference: list[tuple[float, float]],
    root: Path | None = None,
    recipe: dict[str, Any] | None = None,
    intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if recipe is None:
        recipe = recipe_metadata(config)
    if intake is None:
        intake = lab_intake(root, config)
    scenario = demo_scenario(root, config)
    weights = config.get("weights", {})
    predictions = [(k, dispersion(k, params)) for k, _ in reference]
    mse = sum((pred - target) ** 2 for (_, pred), (_, target) in zip(predictions, reference)) / len(reference)
    rmse = math.sqrt(mse)
    group_velocity = finite_difference_group_velocity(params)
    target_velocity = float(config.get("target_group_velocity", 1.35))
    velocity_error = abs(group_velocity - target_velocity)
    damping_penalty = max(0.0, params.get("damping", 0.0) - 0.03)
    stability_penalty = 0.0
    if params["exchange_stiffness"] <= 0:
        stability_penalty += 2.0
    if params["anisotropy"] < 0 or params["field"] < 0:
        stability_penalty += 1.0

    objective = (
        float(weights.get("rmse", 1.0)) * rmse
        + float(weights.get("group_velocity", 0.08)) * velocity_error
        + float(weights.get("damping", 0.03)) * damping_penalty
        + stability_penalty
    )
    dispersion_score = 1.0 / (1.0 + objective)
    plausibility = plausibility_checks(
        params=params,
        config=config,
        reference_count=len(reference),
        rmse=rmse,
        group_velocity=group_velocity,
    )
    lab_objective = lab_objective_components(
        params=params,
        config=config,
        rmse=rmse,
        velocity_error=velocity_error,
        plausibility=plausibility,
    )
    literature = literature_search(
        root=root,
        config=config,
        params=params,
        material_family=plausibility["material_family"],
        process_route=plausibility["process_route"],
        recipe=recipe,
        propagation_length=plausibility["propagation_length_proxy"],
    )
    database = material_database_search(
        root=root,
        config=config,
        params=params,
        material_family=plausibility["material_family"],
        process_route=plausibility["process_route"],
        recipe=recipe,
        propagation_length=plausibility["propagation_length_proxy"],
    )
    simulator = run_simulator_backend(config, params, reference)
    evidence = list(plausibility["evidence"])
    if literature["hits"]:
        evidence.append(
            {
                "type": "literature_notes",
                "source": literature["hits"][0]["source"],
                "supports": literature["hits"][0]["supports"],
                "citation": literature["hits"][0]["citation"],
                "search_score": literature["hits"][0]["score"],
            }
        )
    if database["matches"]:
        evidence.append(
            {
                "type": "database_evidence",
                "source": f"materials_database:{database['matches'][0]['material_id']}",
                "supports": database["matches"][0]["notes"],
                "match_score": database["matches"][0]["score"],
            }
        )
    if simulator["status"] == "completed":
        evidence.append(
            {
                "type": "simulation_output",
                "source": f"simulator:{simulator['backend']}",
                "supports": "Stable simulator abstraction ran the analytic dispersion backend.",
                "rmse": simulator["rmse"],
                "command": simulator["command"],
            }
        )
    evidence_requirements = assess_claim_support(
        evidence=evidence,
        failures=plausibility["plausibility_failures"],
        lab_score=lab_objective["score"],
        physics_score=plausibility["physics_score"],
        plausibility_score=plausibility["plausibility_score"],
        objective_components=lab_objective["components"],
        config=config,
    )
    result = {
        "label": label,
        "origin": origin,
        "score": lab_objective["score"],
        "metric": "lab_relevant_magnonics_score",
        "direction": "maximize",
        "objective": (
            "Maximize propagation-length proxy and low damping while preserving "
            "dispersion/FMR constraints, useful anisotropy, and plausibility."
        ),
        "objective_components": lab_objective["components"],
        "objective_weights": lab_objective["weights"],
        "objective_targets": lab_objective["targets"],
        "dispersion_score": dispersion_score,
        "physics_score": plausibility["physics_score"],
        "plausibility_score": plausibility["plausibility_score"],
        "plausibility_failures": plausibility["plausibility_failures"],
        "evidence": evidence,
        "propagation_model": plausibility["propagation_model"],
        "fmr_constraints": plausibility["fmr_constraints"],
        "material_family_schema": plausibility["material_family_schema"],
        "temperature_dependence": plausibility["temperature_dependence"],
        "process_constraints": plausibility["process_constraints"],
        "literature_search": literature,
        "material_database": database,
        "simulator": simulator,
        "demo_scenario": scenario,
        "lab_intake": intake,
        "evidence_requirements": evidence_requirements,
        "claim_status": evidence_requirements["claim_status"],
        "can_report_promising": evidence_requirements["can_report_promising"],
        "rmse": rmse,
        "group_velocity": group_velocity,
        "target_group_velocity": target_velocity,
        "propagation_length_proxy": plausibility["propagation_length_proxy"],
        "resonance_frequency": plausibility["resonance_frequency"],
        "material_family": plausibility["material_family"],
        "process_route": plausibility["process_route"],
        "damping_penalty": damping_penalty,
        "stability_penalty": stability_penalty,
        "parameters": params,
    }
    result["pre_screening_pipeline"] = build_pre_screening_pipeline(result)
    result["human_review_gates"] = human_review_gates(config, intake, result)
    result["failure_memory"] = classify_failure_memory(result)
    return result


def load_candidate_params(path: Path) -> dict[str, float]:
    return {k: float(v) for k, v in load_simple_yaml(path).items()}


def solve_3x3(matrix: list[list[float]], vector: list[float]) -> list[float]:
    rows = [matrix[i][:] + [vector[i]] for i in range(3)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda row: abs(rows[row][col]))
        rows[col], rows[pivot] = rows[pivot], rows[col]
        if abs(rows[col][col]) < 1e-12:
            raise ValueError("reference fit is singular")
        divisor = rows[col][col]
        rows[col] = [value / divisor for value in rows[col]]
        for row in range(3):
            if row == col:
                continue
            factor = rows[row][col]
            rows[row] = [value - factor * rows[col][idx] for idx, value in enumerate(rows[row])]
    return [rows[i][3] for i in range(3)]


def fit_reference_dispersion(reference: list[tuple[float, float]], base_params: dict[str, float]) -> dict[str, float]:
    sums = {
        "n": float(len(reference)),
        "k": sum(k for k, _ in reference),
        "k2": sum(k**2 for k, _ in reference),
        "k3": sum(k**3 for k, _ in reference),
        "k4": sum(k**4 for k, _ in reference),
        "y": sum(y for _, y in reference),
        "ky": sum(k * y for k, y in reference),
        "k2y": sum(k**2 * y for k, y in reference),
    }
    offset, dmi, exchange = solve_3x3(
        [
            [sums["n"], sums["k"], sums["k2"]],
            [sums["k"], sums["k2"], sums["k3"]],
            [sums["k2"], sums["k3"], sums["k4"]],
        ],
        [sums["y"], sums["ky"], sums["k2y"]],
    )
    field = clamp(base_params.get("field", 0.18), 0.02, max(0.02, offset - 0.02))
    anisotropy = max(0.02, offset - field)
    return {
        "exchange_stiffness": exchange,
        "anisotropy": anisotropy,
        "dmi": dmi,
        "damping": min(base_params.get("damping", 0.045), float(PHYSICS_RULES["damping"]["ideal"][1])),
        "field": field,
    }


def generated_candidate_inputs(
    base_params: dict[str, float],
    reference: list[tuple[float, float]],
    root: Path | None = None,
    config: dict[str, Any] | None = None,
) -> list[tuple[str, str, dict[str, float]]]:
    low_damping = dict(base_params)
    low_damping["damping"] = min(base_params.get("damping", 0.045), 0.025)

    dispersion_matched = fit_reference_dispersion(reference, base_params)
    balanced = dict(dispersion_matched)
    balanced["damping"] = min(dispersion_matched["damping"], 0.025)

    candidates = [
        ("editable_candidate", "candidate/material_params.yaml", base_params),
        ("low_damping_variant", "model_speculation: lower damping at same dispersion parameters", low_damping),
        ("dispersion_matched_low_damping_variant", "model_speculation: quadratic fit to reference plus low damping", balanced),
    ]
    if root is not None and config is not None:
        material_family = str(config.get("material_family", LAB_DEFAULTS["material_family"]))
        for row in load_material_database(root, config):
            if row.get("material_family") != material_family:
                continue
            database_params = dict(base_params)
            database_params["damping"] = min(
                max(base_params.get("damping", 0.0), float(row["damping_min"])),
                float(row["damping_max"]),
            )
            database_params["anisotropy"] = min(
                max(base_params.get("anisotropy", 0.0), float(row["anisotropy_min"])),
                float(row["anisotropy_max"]),
            )
            database_params["exchange_stiffness"] = min(
                max(base_params.get("exchange_stiffness", 0.0), float(row["exchange_min"])),
                float(row["exchange_max"]),
            )
            database_params["dmi"] = min(max(base_params.get("dmi", 0.0), float(row["dmi_min"])), float(row["dmi_max"]))
            candidates.append((f"database_{row['material_id']}", f"materials_database:{row['material_id']}", database_params))
            break
    return candidates


def recipe_metadata(config: dict[str, Any]) -> dict[str, Any]:
    recipe = config.get("recipe", {})
    if not isinstance(recipe, dict):
        recipe = {}
    return {
        "composition": recipe.get("composition", LAB_DEFAULTS["composition"]),
        "thickness_nm": float(recipe.get("thickness_nm", LAB_DEFAULTS["thickness_nm"])),
        "stack": recipe.get("stack", LAB_DEFAULTS["stack"]),
        "cap_layer": recipe.get("cap_layer", LAB_DEFAULTS["cap_layer"]),
        "substrate": recipe.get("substrate", LAB_DEFAULTS["substrate"]),
        "sputter_pressure_mTorr": float(recipe.get("sputter_pressure_mTorr", LAB_DEFAULTS["sputter_pressure_mTorr"])),
        "sputter_power_W": float(recipe.get("sputter_power_W", LAB_DEFAULTS["sputter_power_W"])),
        "anneal_temperature_C": float(recipe.get("anneal_temperature_C", LAB_DEFAULTS["anneal_temperature_C"])),
        "anneal": recipe.get("anneal", LAB_DEFAULTS["anneal"]),
        "next_measurement": recipe.get("next_measurement", LAB_DEFAULTS["next_measurement"]),
        "roughness_risk": recipe.get("roughness_risk", "unknown until AFM is measured"),
    }


def candidate_report_summary(candidate: dict[str, Any], recipe: dict[str, Any], rank: int) -> dict[str, Any]:
    evidence_sources = [item["source"] for item in candidate["evidence"]]
    hard_failures = [
        item["rule"] for item in candidate["plausibility_failures"] if item.get("severity") == "error"
    ]
    return {
        "rank": rank,
        "label": candidate["label"],
        "origin": candidate["origin"],
        "score": candidate["score"],
        "claim_status": candidate["claim_status"],
        "can_report_promising": candidate["can_report_promising"],
        "human_review_status": candidate["human_review_gates"]["overall_status"],
        "can_promote_candidate": candidate["human_review_gates"]["can_promote_candidate"],
        "composition": recipe["composition"],
        "thickness_nm": recipe["thickness_nm"],
        "stack": recipe["stack"],
        "cap_layer": recipe["cap_layer"],
        "substrate": recipe["substrate"],
        "anneal": recipe["anneal"],
        "predicted_damping": candidate["parameters"]["damping"],
        "anisotropy": candidate["parameters"]["anisotropy"],
        "propagation_length_proxy": candidate["propagation_length_proxy"],
        "lifetime": candidate["propagation_model"]["lifetime"],
        "fmr_linewidth": candidate["fmr_constraints"]["linewidth"],
        "anisotropy_field": candidate["fmr_constraints"]["anisotropy_field"],
        "material_schema": candidate["material_family_schema"]["schema"],
        "process_score": candidate["process_constraints"]["score"],
        "temperature_score": candidate["temperature_dependence"]["score"],
        "literature_hits": len(candidate["literature_search"]["hits"]),
        "database_matches": len(candidate["material_database"]["matches"]),
        "simulator_status": candidate["simulator"]["status"],
        "roughness_risk": recipe["roughness_risk"],
        "why_plausible": [
            f"physics_score={candidate['physics_score']:.3f}",
            f"plausibility_score={candidate['plausibility_score']:.3f}",
            f"propagation_length_proxy={candidate['propagation_length_proxy']:.3f}",
            f"fmr_linewidth={candidate['fmr_constraints']['linewidth']:.4f}",
            f"process_score={candidate['process_constraints']['score']:.3f}",
            f"literature_hits={len(candidate['literature_search']['hits'])}",
            f"database_matches={len(candidate['material_database']['matches'])}",
        ],
        "evidence": evidence_sources,
        "failure_modes": hard_failures or candidate["evidence_requirements"]["blocked_reasons"],
        "uncertainty": [
            "Synthetic analytic evaluator only.",
            "No AFM roughness, hysteresis, FMR linewidth, temperature dependence, or fabrication data measured.",
        ],
        "next_lab_measurement": recipe["next_measurement"],
        "human_must_verify": [
            "Composition, thickness, cap continuity, and roughness after deposition.",
            "Magnetic ordering and anisotropy from hysteresis or MOKE.",
            "Gilbert damping and linewidth-vs-frequency from FMR before trusting propagation claims.",
        ],
    }


def ranked_candidates(
    config: dict[str, Any],
    params: dict[str, float],
    reference: list[tuple[float, float]],
    root: Path | None = None,
    recipe: dict[str, Any] | None = None,
    intake: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    scored = [
        score_material_candidate(label, origin, candidate_params, config, reference, root=root, recipe=recipe, intake=intake)
        for label, origin, candidate_params in generated_candidate_inputs(params, reference, root=root, config=config)
    ]
    return sorted(scored, key=lambda item: item["score"], reverse=True)


def render_candidate_report(primary: dict[str, Any], ranked: list[dict[str, Any]], recipe: dict[str, Any]) -> str:
    summaries = [candidate_report_summary(candidate, recipe, idx + 1) for idx, candidate in enumerate(ranked)]
    evaluated_evidence = [item for item in primary["evidence"] if item["type"] in {"reference_data", "evaluator_output", "simulation_output"}]
    support_evidence = [item for item in primary["evidence"] if item["type"] in {"literature_notes", "database_evidence", "material_schema", "process_window", "lab_defaults"}]
    scenario = primary.get("demo_scenario", {})
    lines = [
        "# Magnonics Candidate Report",
        "",
        "Do not trust until measured. This report ranks analytic benchmark candidates only; it is not lab validation.",
        "",
        "## Executive Summary",
        "",
        f"- Primary candidate: {primary['label']} ({primary['claim_status']})",
        f"- Lab objective score: {primary['score']:.3f}",
        f"- Human promotion gate: {primary['human_review_gates']['overall_status']}",
        f"- Target property: {primary['lab_intake']['target_property']}",
        f"- Demo scenario: {scenario.get('title', 'not configured')} ({scenario.get('status', 'not_configured')})",
        "- Required caveat: do not trust any candidate until AFM, hysteresis/MOKE, and FMR measurements exist.",
        f"- Scenario caveat: {scenario.get('caveat', 'not configured')}",
        "",
        "## Ranked Candidates",
        "",
        "| Rank | Candidate | Score | Claim | Review | Damping | Linewidth | Lifetime | Propagation | Main failure modes |",
        "| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for summary in summaries:
        failures = "; ".join(summary["failure_modes"]) if summary["failure_modes"] else "none from evaluator"
        lines.append(
            "| {rank} | {label} | {score:.3f} | {claim_status} | {human_review_status} | {predicted_damping:.4f} | "
            "{fmr_linewidth:.4f} | {lifetime:.3f} | {propagation_length_proxy:.3f} | {failures} |".format(
                **summary,
                failures=failures,
            )
        )

    lines.extend(
        [
            "",
            "## Evaluated Evidence",
            "",
        ]
    )
    for item in evaluated_evidence:
        lines.append(f"- {item['type']}: {item['source']} - {item['supports']}")

    lines.extend(
        [
            "",
            "## Literature And Database Support",
            "",
        ]
    )
    for item in support_evidence:
        lines.append(f"- {item['type']}: {item['source']} - {item['supports']}")

    lines.extend(
        [
            "",
            "## Demo Scenario",
            "",
            f"- Path: {scenario.get('path', '')}",
            f"- Material system: {scenario.get('material_system', '')}",
            f"- Spin-dynamics axes: {', '.join(scenario.get('spin_dynamics_axes', []))}",
            f"- Temperature axis C: {', '.join(str(item) for item in scenario.get('temperature_axis_C', []))}",
            f"- Candidate loop: {', '.join(scenario.get('candidate_loop', []))}",
            f"- Success signal: {scenario.get('primary_success_signal', '')}",
            f"- Forbidden claim: {scenario.get('forbidden_claim', '')}",
            f"- Human review focus: {scenario.get('human_review_focus', '')}",
            "",
            "## Model Speculation",
            "",
            "- Generated variants are analytic what-if recipes, not measured films.",
            "- Propagation length is derived from group velocity and a damping/linewidth lifetime model.",
            "- Smooth morphology and process quality remain unknown until AFM and deposition logs exist.",
            "",
            "## Physics Checks",
            "",
            f"- FMR linewidth: {primary['fmr_constraints']['linewidth']:.4f}",
            f"- Anisotropy field: {primary['fmr_constraints']['anisotropy_field']:.4f}",
            f"- Field dependence monotonic: {primary['fmr_constraints']['field_dependence_monotonic']}",
            f"- Material schema: {primary['material_family_schema']['schema']}",
            f"- Process score: {primary['process_constraints']['score']:.3f}",
            f"- Temperature score: {primary['temperature_dependence']['score']:.3f}",
            "",
            "## Research Assistant Checks",
            "",
            f"- Intake status: {primary['lab_intake']['status']} ({primary['lab_intake']['path']})",
            f"- Literature hits: {len(primary['literature_search']['hits'])}",
            f"- Material database matches: {len(primary['material_database']['matches'])}",
            f"- Simulator backend: {primary['simulator']['backend']} ({primary['simulator']['status']})",
            "- Pre-screening pipeline:",
        ]
    )
    for stage in primary["pre_screening_pipeline"]:
        lines.append(f"  - {stage['stage']}: {stage['status']} - {stage['reason']}")
    lines.extend(
        [
            "",
            "## Human Review Gates",
            "",
            f"- Reviewer: {primary['human_review_gates']['reviewer']}",
            f"- Overall status: {primary['human_review_gates']['overall_status']}",
            f"- Can run deeper simulation: {primary['human_review_gates']['can_run_deeper_simulation']}",
            f"- Can promote candidate: {primary['human_review_gates']['can_promote_candidate']}",
        ]
    )
    for gate in primary["human_review_gates"]["gates"]:
        lines.append(f"  - {gate['gate']}: {gate['status']} - {gate['reason']}")
    lines.extend(
        [
            "",
            "## Next Lab Measurements",
            "",
            f"- {recipe['next_measurement']}",
            "- Verify the cap/stack and film thickness before interpreting spin-transport proxies.",
            "- Re-run the ranking after measured linewidth, roughness, and hysteresis data are added.",
        ]
    )
    return "\n".join(lines) + "\n"


def evaluate(config_path: Path) -> dict[str, Any]:
    config = load_simple_yaml(config_path)
    root = config_path.parent.parent
    candidate_path = root / str(config["candidate"])
    reference_path = root / str(config["reference"])
    output_dir = root / str(config.get("outputs", "outputs"))
    params = load_candidate_params(candidate_path)
    reference = load_reference(reference_path)
    recipe = recipe_metadata(config)
    intake = lab_intake(root, config)
    ranked = ranked_candidates(config, params, reference, root=root, recipe=recipe, intake=intake)
    result = next(candidate for candidate in ranked if candidate["label"] == "editable_candidate")
    result["ranked_candidates"] = [
        candidate_report_summary(candidate, recipe, idx + 1) for idx, candidate in enumerate(ranked)
    ]
    failure_memory = [record for candidate in ranked for record in candidate["failure_memory"]]
    result["failure_memory"] = failure_memory
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "metrics.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (output_dir / "ranked_candidates.json").write_text(json.dumps(result["ranked_candidates"], indent=2) + "\n", encoding="utf-8")
    (output_dir / "failure_memory.json").write_text(json.dumps(failure_memory, indent=2) + "\n", encoding="utf-8")
    (output_dir / "lab_intake_summary.json").write_text(json.dumps(intake, indent=2) + "\n", encoding="utf-8")
    (output_dir / "candidate_report.md").write_text(
        render_candidate_report(result, ranked, recipe),
        encoding="utf-8",
    )
    with (output_dir / "predicted_dispersion.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["k", "frequency"])
        writer.writerows((k, dispersion(k, params)) for k, _ in reference)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/example.yaml")
    args = parser.parse_args()
    result = evaluate(Path(args.config).resolve())
    print(f"score: {result['score']:.6f}")
    print(f"physics_score: {result['physics_score']:.6f}")
    print(f"plausibility_score: {result['plausibility_score']:.6f}")
    print(f"claim_status: {result['claim_status']}")
    print(f"rmse: {result['rmse']:.6f}")
    print("metrics: outputs/metrics.json")
    print("report: outputs/candidate_report.md")


if __name__ == "__main__":
    main()
