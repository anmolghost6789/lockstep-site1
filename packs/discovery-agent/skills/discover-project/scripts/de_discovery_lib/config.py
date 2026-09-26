"""Configuration contract and defaults."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .io import DiscoveryError, load_yaml
from .security import scan_text


POLICY_DECISIONS = {"allow", "ask", "deny"}
READINESS_TARGETS = {"discovery-only", "requirements-ready", "design-ready"}
PROVIDERS = {"auto", "mcp", "cli", "offline"}
EVIDENCE_MODES = {"snapshot", "reference"}
RESEARCH_MODES = {"off", "official-only", "official-first", "open-with-review"}
DISCOVERY_FACETS = {
    "business",
    "landscape",
    "data",
    "acquisition",
    "processing",
    "consumption",
    "quality",
    "governance",
    "operations",
    "platform",
    "economics",
    "change",
}
ARCHETYPE_FACETS: dict[str, set[str]] = {
    "general": {"business", "landscape", "data", "quality", "governance", "operations"},
    "greenfield-data-product": {
        "business",
        "data",
        "acquisition",
        "processing",
        "consumption",
        "quality",
        "governance",
        "operations",
        "platform",
        "economics",
    },
    "source-onboarding": {
        "business",
        "landscape",
        "data",
        "acquisition",
        "quality",
        "governance",
        "operations",
        "platform",
    },
    "brownfield-change": {
        "business",
        "landscape",
        "data",
        "processing",
        "consumption",
        "quality",
        "governance",
        "operations",
        "change",
    },
    "migration-modernization": {
        "business",
        "landscape",
        "data",
        "processing",
        "consumption",
        "quality",
        "governance",
        "operations",
        "platform",
        "economics",
        "change",
    },
    "platform-modernization": {
        "landscape",
        "governance",
        "operations",
        "platform",
        "economics",
        "change",
    },
    "data-sharing": {
        "business",
        "data",
        "consumption",
        "quality",
        "governance",
        "operations",
    },
    "quality-reliability-remediation": {
        "business",
        "landscape",
        "data",
        "processing",
        "quality",
        "operations",
    },
    "governance-compliance": {
        "business",
        "landscape",
        "data",
        "quality",
        "governance",
        "operations",
    },
    "performance-cost-optimization": {
        "landscape",
        "processing",
        "consumption",
        "operations",
        "platform",
        "economics",
    },
    "decommission-archive": {
        "business",
        "landscape",
        "data",
        "consumption",
        "governance",
        "operations",
        "change",
    },
}

DEFAULT_CONFIG: dict[str, Any] = {
    "version": "1",
    "project_id": "",
    "objective": "",
    "readiness_target": "requirements-ready",
    "knowledge_root": "knowledge",
    "engagement": {
        "archetypes": ["general"],
        "required_facets": [],
    },
    "inputs": {
        "roots": [],
        "evidence_mode": "snapshot",
        "max_files": 500,
        "max_file_bytes": 104_857_600,
        "max_extracted_chars": 2_000_000,
        "max_tabular_rows": 2_000,
    },
    "discovery": {
        "seeds": [],
        "include": {"systems": [], "catalogs": [], "schemas": [], "assets": []},
        "exclude": {"systems": [], "catalogs": [], "schemas": [], "assets": []},
        "limits": {
            "max_candidate_assets": 100,
            "max_deep_profiles": 15,
            "lineage_depth": 1,
            "allow_row_sampling": False,
        },
        "stop_when": [
            "requested_readiness_supported",
            "material_contradictions_visible",
            "remaining_gaps_owned_or_non_blocking",
        ],
    },
    "research": {
        "mode": "official-first",
        "allowed_domains": [],
        "denied_domains": [],
        "max_searches_per_run": 20,
        "max_pages_per_question": 5,
        "default_stale_after_days": 30,
        "allow_sensitive_query_terms": False,
    },
    "databricks": {
        "provider": "auto",
        "profile": "DEFAULT",
        "workspace_hint": None,
        "agent_resource_prefix": "de_discovery_",
        "policy": {
            "read": "allow",
            "create_owned": "allow",
            "modify_existing": "ask",
            "manage_permissions": "ask",
            "delete": "deny",
        },
    },
    "ownership": {"discovery_owner": None, "boundary_approver": None},
}


def _merge(default: dict[str, Any], supplied: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(default)
    for key, value in supplied.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def _require_list(value: Any, label: str) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise DiscoveryError(f"{label} must be a list of strings")


def _positive_int(value: Any, label: str, *, minimum: int = 1) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise DiscoveryError(f"{label} must be an integer >= {minimum}")


def required_facets(config: dict[str, Any]) -> set[str]:
    engagement = config["engagement"]
    facets = set(engagement["required_facets"])
    for archetype in engagement["archetypes"]:
        facets.update(ARCHETYPE_FACETS.get(archetype, set()))
    return facets


def validate_config(config: dict[str, Any]) -> None:
    if str(config.get("version")) != "1":
        raise DiscoveryError("Unsupported config version; expected '1'")
    for label in ("project_id", "objective"):
        if not isinstance(config.get(label), str):
            raise DiscoveryError(f"{label} must be a string")
    if config["readiness_target"] not in READINESS_TARGETS:
        raise DiscoveryError(f"readiness_target must be one of {sorted(READINESS_TARGETS)}")

    engagement = config["engagement"]
    _require_list(engagement["archetypes"], "engagement.archetypes")
    _require_list(engagement["required_facets"], "engagement.required_facets")
    if not engagement["archetypes"]:
        raise DiscoveryError("engagement.archetypes must name at least one project archetype")
    for archetype in engagement["archetypes"]:
        if not archetype or any(
            character not in "abcdefghijklmnopqrstuvwxyz0123456789-"
            for character in archetype
        ):
            raise DiscoveryError(
                "engagement.archetypes values must use lowercase letters, digits, and hyphens"
            )
        if archetype not in ARCHETYPE_FACETS and not engagement["required_facets"]:
            raise DiscoveryError(
                f"Custom archetype {archetype!r} requires explicit engagement.required_facets"
            )
    unknown_facets = set(engagement["required_facets"]) - DISCOVERY_FACETS
    if unknown_facets:
        raise DiscoveryError(
            f"Unknown engagement.required_facets: {sorted(unknown_facets)}"
        )

    inputs = config["inputs"]
    if inputs["evidence_mode"] not in EVIDENCE_MODES:
        raise DiscoveryError(f"inputs.evidence_mode must be one of {sorted(EVIDENCE_MODES)}")
    _require_list(inputs["roots"], "inputs.roots")
    for field in ("max_files", "max_file_bytes", "max_extracted_chars", "max_tabular_rows"):
        _positive_int(inputs[field], f"inputs.{field}")

    discovery = config["discovery"]
    _require_list(discovery["seeds"], "discovery.seeds")
    for direction in ("include", "exclude"):
        for dimension in ("systems", "catalogs", "schemas", "assets"):
            _require_list(discovery[direction][dimension], f"discovery.{direction}.{dimension}")
    for field in ("max_candidate_assets", "max_deep_profiles"):
        _positive_int(discovery["limits"][field], f"discovery.limits.{field}")
    _positive_int(discovery["limits"]["lineage_depth"], "discovery.limits.lineage_depth", minimum=0)
    if not isinstance(discovery["limits"]["allow_row_sampling"], bool):
        raise DiscoveryError("discovery.limits.allow_row_sampling must be boolean")

    research = config["research"]
    if research["mode"] not in RESEARCH_MODES:
        raise DiscoveryError(f"research.mode must be one of {sorted(RESEARCH_MODES)}")
    _require_list(research["allowed_domains"], "research.allowed_domains")
    _require_list(research["denied_domains"], "research.denied_domains")
    if research["mode"] == "official-only" and not research["allowed_domains"]:
        raise DiscoveryError(
            "research.allowed_domains is required when research.mode is official-only"
        )
    for field in ("max_searches_per_run", "max_pages_per_question", "default_stale_after_days"):
        _positive_int(research[field], f"research.{field}")
    if not isinstance(research["allow_sensitive_query_terms"], bool):
        raise DiscoveryError("research.allow_sensitive_query_terms must be boolean")

    databricks = config["databricks"]
    if databricks["provider"] not in PROVIDERS:
        raise DiscoveryError(f"databricks.provider must be one of {sorted(PROVIDERS)}")
    prefix = databricks["agent_resource_prefix"]
    if not isinstance(prefix, str) or not prefix or not prefix.replace("_", "").isalnum():
        raise DiscoveryError("databricks.agent_resource_prefix must be a non-empty safe prefix")
    for action_class, decision in databricks["policy"].items():
        if action_class not in {
            "read",
            "create_owned",
            "modify_existing",
            "manage_permissions",
            "delete",
        }:
            raise DiscoveryError(f"Unknown Databricks policy class: {action_class}")
        if decision not in POLICY_DECISIONS:
            raise DiscoveryError(
                f"databricks.policy.{action_class} must be one of {sorted(POLICY_DECISIONS)}"
            )


def load_config(path: Path) -> dict[str, Any]:
    findings = scan_text(path.read_text(encoding="utf-8"))
    if findings:
        locations = ", ".join(
            f"line {item.line} ({item.detector})" for item in findings[:10]
        )
        raise DiscoveryError(f"Potential secret detected in config; refused at {locations}")
    config = _merge(DEFAULT_CONFIG, load_yaml(path))
    validate_config(config)
    return config
