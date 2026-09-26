"""Deterministic candidate-priority scoring."""

from __future__ import annotations

from typing import Any

from .io import DiscoveryError


RANGES = {
    "objective_relevance": (0, 5),
    "seed_proximity": (0, 4),
    "authoritative_use": (0, 3),
    "structural_fit": (0, 3),
    "operational_fitness": (0, 2),
    "evidence_risk": (-5, 0),
}


def score_candidates(value: Any) -> list[dict[str, Any]]:
    candidates = value.get("candidates") if isinstance(value, dict) else value
    if not isinstance(candidates, list):
        raise DiscoveryError("Candidate input must be a list or a mapping with candidates")

    results: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise DiscoveryError(f"Candidate {index} must be a mapping")
        name = candidate.get("name")
        components = candidate.get("scores")
        reasons = candidate.get("reasons")
        if not isinstance(name, str) or not name.strip():
            raise DiscoveryError(f"Candidate {index} requires a name")
        if not isinstance(components, dict):
            raise DiscoveryError(f"Candidate {name!r} requires scores")
        if not isinstance(reasons, dict):
            raise DiscoveryError(f"Candidate {name!r} requires component reasons")

        normalized: dict[str, int] = {}
        for component, (minimum, maximum) in RANGES.items():
            score = components.get(component)
            if isinstance(score, bool) or not isinstance(score, int):
                raise DiscoveryError(f"{name}.{component} must be an integer")
            if not minimum <= score <= maximum:
                raise DiscoveryError(
                    f"{name}.{component} must be between {minimum} and {maximum}"
                )
            reason = reasons.get(component)
            if not isinstance(reason, str) or not reason.strip():
                raise DiscoveryError(f"{name}.{component} requires a reason")
            normalized[component] = score

        results.append(
            {
                "name": name,
                "priority": sum(normalized.values()),
                "scores": normalized,
                "reasons": {key: reasons[key] for key in RANGES},
                "blocking_risk": normalized["evidence_risk"] <= -4,
            }
        )

    return sorted(
        results,
        key=lambda item: (
            item["blocking_risk"],
            -item["priority"],
            -item["scores"]["objective_relevance"],
            -item["scores"]["seed_proximity"],
            item["name"].casefold(),
        ),
    )
