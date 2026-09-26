"""Structured handoff contracts for specialized discovery concepts."""

from __future__ import annotations

from typing import Any

from .ingestion import validate_ingestion_spec


COMPLETENESS_STATUSES = {"supported", "partial", "missing", "not_applicable"}
CONTRACT_STATUSES = {
    "assessed",
    "feasible",
    "approved",
    "implementation-ready",
    "deployed",
}
MIGRATION_DISPOSITIONS = {
    "retire",
    "retain",
    "federate",
    "rehost",
    "convert",
    "refactor",
    "redesign",
    "undecided",
}
MIGRATION_COMPLEXITIES = {"low", "medium", "high", "very-high", "unknown"}

SOURCE_SYSTEM_SECTIONS = {
    "identity_ownership",
    "connectivity_access",
    "structure_scale",
    "change_capabilities",
    "security_governance",
    "operational_constraints",
}
ACQUISITION_SECTIONS = {
    "source_scope",
    "target_mapping",
    "delivery",
    "change_capture",
    "schema",
    "quality_reconciliation",
    "security_governance",
    "operations_recovery",
}
MIGRATION_ASSESSMENT_SECTIONS = {
    "drivers_scope",
    "estate_inventory",
    "dependencies",
    "usage_disposition",
    "compatibility",
    "target_mapping",
    "economics",
    "risks_assumptions",
}
MIGRATION_UNIT_SECTIONS = {
    "scope",
    "dependencies",
    "disposition",
    "data",
    "code",
    "consumers",
    "validation",
    "cutover_rollback",
}
MIGRATION_PLAN_SECTIONS = {
    "waves",
    "sequencing",
    "coexistence",
    "validation",
    "cutover_rollback",
    "decommission",
}


def _validate_sections(
    metadata: dict[str, Any],
    *,
    field: str,
    required: set[str],
    path: str,
    errors: list[dict[str, str]],
) -> None:
    block = metadata.get(field)
    if not isinstance(block, dict):
        errors.append({"path": path, "message": f"{field} must be a mapping"})
        return
    missing = sorted(required - set(block))
    if missing:
        errors.append(
            {
                "path": path,
                "message": f"{field} is missing required sections: {missing}",
            }
        )
    for section in sorted(required.intersection(block)):
        value = block[section]
        if not isinstance(value, dict):
            errors.append(
                {
                    "path": path,
                    "message": f"{field}.{section} must be a mapping",
                }
            )
            continue
        status = value.get("status")
        if status not in COMPLETENESS_STATUSES:
            errors.append(
                {
                    "path": path,
                    "message": (
                        f"{field}.{section}.status must be one of "
                        f"{sorted(COMPLETENESS_STATUSES)}"
                    ),
                }
            )
        gaps = value.get("gaps")
        if gaps is not None and (
            not isinstance(gaps, list) or any(not isinstance(item, str) for item in gaps)
        ):
            errors.append(
                {
                    "path": path,
                    "message": f"{field}.{section}.gaps must be a list of strings",
                }
            )


def validate_specialized_concept(
    metadata: dict[str, Any],
    *,
    role: str | None,
    path: str,
    errors: list[dict[str, str]],
) -> None:
    if metadata.get("status") == "deprecated":
        return
    extension = metadata.get("de_agents")
    extension = extension if isinstance(extension, dict) else {}

    if role == "source_system_profile":
        _validate_sections(
            metadata,
            field="source_system",
            required=SOURCE_SYSTEM_SECTIONS,
            path=path,
            errors=errors,
        )
        return

    if role == "acquisition_contract":
        if str(extension.get("contract_version")) != "1.0":
            errors.append(
                {
                    "path": path,
                    "message": "acquisition contract requires de_agents.contract_version: '1.0'",
                }
            )
        if extension.get("contract_status") not in CONTRACT_STATUSES:
            errors.append(
                {
                    "path": path,
                    "message": (
                        "acquisition contract requires de_agents.contract_status in "
                        f"{sorted(CONTRACT_STATUSES)}"
                    ),
                }
            )
        _validate_sections(
            metadata,
            field="acquisition",
            required=ACQUISITION_SECTIONS,
            path=path,
            errors=errors,
        )
        return

    if role == "ingestion_spec":
        validate_ingestion_spec(metadata, path=path, errors=errors)
        return

    if role == "migration_assessment":
        _validate_sections(
            metadata,
            field="migration_assessment",
            required=MIGRATION_ASSESSMENT_SECTIONS,
            path=path,
            errors=errors,
        )
        return

    if role == "migration_unit":
        disposition = extension.get("migration_disposition")
        if disposition not in MIGRATION_DISPOSITIONS:
            errors.append(
                {
                    "path": path,
                    "message": (
                        "migration unit requires de_agents.migration_disposition in "
                        f"{sorted(MIGRATION_DISPOSITIONS)}"
                    ),
                }
            )
        complexity = extension.get("migration_complexity")
        if complexity not in MIGRATION_COMPLEXITIES:
            errors.append(
                {
                    "path": path,
                    "message": (
                        "migration unit requires de_agents.migration_complexity in "
                        f"{sorted(MIGRATION_COMPLEXITIES)}"
                    ),
                }
            )
        _validate_sections(
            metadata,
            field="migration_unit",
            required=MIGRATION_UNIT_SECTIONS,
            path=path,
            errors=errors,
        )
        return

    if role == "migration_plan":
        _validate_sections(
            metadata,
            field="migration_plan",
            required=MIGRATION_PLAN_SECTIONS,
            path=path,
            errors=errors,
        )
