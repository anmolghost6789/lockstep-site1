"""Validation and deterministic export for ingestion specifications."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Iterable

import yaml

from .io import DiscoveryError, atomic_write_text, ensure_within
from .security import scan_text


INGESTION_SPEC_STATUSES = {
    "candidate",
    "implementation-ready",
    "approved",
    "deployed",
}
LOAD_TYPES = {
    "append",
    "cdc",
    "federated",
    "full",
    "incremental",
    "snapshot",
    "streaming",
}
ASSET_TYPES = {"api", "file", "share", "stream", "table"}
DELETE_MODES = {"hard", "none", "not_applicable", "soft"}
SCHEDULE_UNITS = {"minutes", "hours", "days", "weeks"}
READY_STATUSES = {"implementation-ready", "approved", "deployed"}


def _error(errors: list[dict[str, str]], path: str, message: str) -> None:
    errors.append({"path": path, "message": message})


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_string_list(
    value: Any,
    *,
    path: str,
    field: str,
    errors: list[dict[str, str]],
    require_non_empty: bool = False,
) -> bool:
    valid = isinstance(value, list) and all(_non_empty_string(item) for item in value)
    if not valid or (require_non_empty and not value):
        suffix = " and cannot be empty" if require_non_empty else ""
        _error(errors, path, f"{field} must be a list of non-empty strings{suffix}")
        return False
    return True


def _validate_source(
    source: Any,
    *,
    index: int,
    ready: bool,
    path: str,
    errors: list[dict[str, str]],
) -> str | None:
    label = f"ingestion.sources[{index}]"
    if not isinstance(source, dict):
        _error(errors, path, f"{label} must be a mapping")
        return None

    for field in ("connection_id", "source_type"):
        if not _non_empty_string(source.get(field)):
            _error(errors, path, f"{label}.{field} must be a non-empty string")

    connection_id = source.get("connection_id")
    source_type = source.get("source_type")
    if ready:
        if not _non_empty_string(source.get("connection_name")):
            _error(
                errors,
                path,
                f"{label}.connection_name is required when the spec is implementation-ready",
            )
        if source_type == "rdbms":
            for field in ("engine", "database"):
                if not _non_empty_string(source.get(field)):
                    _error(
                        errors,
                        path,
                        f"{label}.{field} is required for an implementation-ready RDBMS source",
                    )

    port = source.get("port")
    if port is not None and (not isinstance(port, int) or isinstance(port, bool) or port <= 0):
        _error(errors, path, f"{label}.port must be a positive integer")
    return connection_id if _non_empty_string(connection_id) else None


def _validate_schedule(
    schedule: Any,
    *,
    label: str,
    path: str,
    errors: list[dict[str, str]],
) -> None:
    if not isinstance(schedule, dict):
        _error(errors, path, f"{label}.schedule must be a mapping")
        return
    mode = schedule.get("mode")
    if not _non_empty_string(mode):
        _error(errors, path, f"{label}.schedule.mode must be a non-empty string")
        return
    if mode == "periodic":
        interval = schedule.get("interval")
        if not isinstance(interval, int) or isinstance(interval, bool) or interval <= 0:
            _error(errors, path, f"{label}.schedule.interval must be a positive integer")
        if schedule.get("unit") not in SCHEDULE_UNITS:
            _error(
                errors,
                path,
                f"{label}.schedule.unit must be one of {sorted(SCHEDULE_UNITS)}",
            )


def _validate_delete_handling(
    value: Any,
    *,
    label: str,
    path: str,
    errors: list[dict[str, str]],
) -> None:
    if not isinstance(value, dict):
        _error(errors, path, f"{label}.delete_handling must be a mapping")
        return
    mode = value.get("mode")
    if mode not in DELETE_MODES:
        _error(
            errors,
            path,
            f"{label}.delete_handling.mode must be one of {sorted(DELETE_MODES)}",
        )
    elif mode == "soft" and not _non_empty_string(value.get("condition")):
        _error(
            errors,
            path,
            f"{label}.delete_handling.condition is required for soft deletes",
        )


def _validate_ready_controls(
    dataset: dict[str, Any],
    *,
    label: str,
    path: str,
    errors: list[dict[str, str]],
) -> None:
    _validate_schedule(dataset.get("schedule"), label=label, path=path, errors=errors)
    _validate_delete_handling(
        dataset.get("delete_handling"),
        label=label,
        path=path,
        errors=errors,
    )

    schema_evolution = dataset.get("schema_evolution")
    if not isinstance(schema_evolution, dict) or not _non_empty_string(
        schema_evolution.get("mode") if isinstance(schema_evolution, dict) else None
    ):
        _error(
            errors,
            path,
            f"{label}.schema_evolution requires a non-empty mode",
        )

    reconciliation = dataset.get("reconciliation")
    if not isinstance(reconciliation, dict):
        _error(errors, path, f"{label}.reconciliation must be a mapping")
    else:
        _validate_string_list(
            reconciliation.get("checks"),
            path=path,
            field=f"{label}.reconciliation.checks",
            errors=errors,
            require_non_empty=True,
        )
        if not _non_empty_string(reconciliation.get("owner")):
            _error(errors, path, f"{label}.reconciliation.owner must be a non-empty string")

    recovery = dataset.get("recovery")
    if not isinstance(recovery, dict):
        _error(errors, path, f"{label}.recovery must be a mapping")
    else:
        for field in ("checkpoint_or_state", "replay_strategy"):
            if not _non_empty_string(recovery.get(field)):
                _error(errors, path, f"{label}.recovery.{field} must be a non-empty string")


def _validate_dataset(
    dataset: Any,
    *,
    index: int,
    connection_ids: set[str],
    ready: bool,
    path: str,
    errors: list[dict[str, str]],
) -> tuple[str, str, str] | None:
    label = f"ingestion.datasets[{index}]"
    if not isinstance(dataset, dict):
        _error(errors, path, f"{label} must be a mapping")
        return None

    for field in ("connection_id", "destination_table", "load_type"):
        if not _non_empty_string(dataset.get(field)):
            _error(errors, path, f"{label}.{field} must be a non-empty string")

    asset_type = dataset.get("asset_type", "table")
    if asset_type not in ASSET_TYPES:
        _error(errors, path, f"{label}.asset_type must be one of {sorted(ASSET_TYPES)}")
    source_fields: tuple[str, ...]
    if asset_type in {"table", "share"}:
        source_fields = ("source_schema", "source_table")
    elif asset_type == "file":
        source_fields = ("source_uri", "file_format")
    elif asset_type == "stream":
        source_fields = ("source_topic",)
    else:
        source_fields = ("source_object",)
    for field in source_fields:
        if not _non_empty_string(dataset.get(field)):
            _error(errors, path, f"{label}.{field} must be a non-empty string")

    connection_id = dataset.get("connection_id")
    if _non_empty_string(connection_id) and connection_id not in connection_ids:
        _error(
            errors,
            path,
            f"{label}.connection_id references unknown source {connection_id!r}",
        )

    load_type = dataset.get("load_type")
    if load_type not in LOAD_TYPES:
        _error(errors, path, f"{label}.load_type must be one of {sorted(LOAD_TYPES)}")

    watermark = dataset.get("watermark_column")
    if watermark is not None and not _non_empty_string(watermark):
        _error(errors, path, f"{label}.watermark_column must be a non-empty string")

    primary_keys = dataset.get("primary_keys")
    if primary_keys is not None:
        _validate_string_list(
            primary_keys,
            path=path,
            field=f"{label}.primary_keys",
            errors=errors,
        )

    if ready:
        for field in ("destination_catalog", "destination_schema"):
            if not _non_empty_string(dataset.get(field)):
                _error(
                    errors,
                    path,
                    f"{label}.{field} is required when the spec is implementation-ready",
                )

        if load_type == "incremental" and asset_type != "file":
            if not _non_empty_string(watermark):
                _error(
                    errors,
                    path,
                    f"{label}.watermark_column is required for incremental ingestion",
                )
            validation = dataset.get("watermark_validation")
            if not isinstance(validation, dict) or validation.get("status") != "supported":
                _error(
                    errors,
                    path,
                    f"{label}.watermark_validation.status must be supported",
                )
            elif validation.get("gaps") not in (None, []):
                _error(
                    errors,
                    path,
                    f"{label}.watermark_validation.gaps must be empty",
                )
            if dataset.get("write_semantics") != "append_only":
                _validate_string_list(
                    primary_keys,
                    path=path,
                    field=f"{label}.primary_keys",
                    errors=errors,
                    require_non_empty=True,
                )
        if load_type == "cdc":
            _validate_string_list(
                primary_keys,
                path=path,
                field=f"{label}.primary_keys",
                errors=errors,
                require_non_empty=True,
            )
            change_capture = dataset.get("change_capture")
            if not isinstance(change_capture, dict) or not _non_empty_string(
                change_capture.get("method") if isinstance(change_capture, dict) else None
            ):
                _error(
                    errors,
                    path,
                    f"{label}.change_capture requires a non-empty method for CDC",
                )
        _validate_ready_controls(dataset, label=label, path=path, errors=errors)

    source_identity = "|".join(str(dataset.get(field, "")) for field in source_fields)
    key_fields = (connection_id, str(asset_type), source_identity)
    if all(_non_empty_string(item) for item in key_fields):
        return str(connection_id), str(asset_type), source_identity
    return None


def validate_ingestion_spec(
    metadata: dict[str, Any],
    *,
    path: str,
    errors: list[dict[str, str]],
) -> None:
    """Validate a neutral, evidence-derived ingestion handoff."""
    extension = metadata.get("de_agents")
    extension = extension if isinstance(extension, dict) else {}
    status = extension.get("spec_status")

    if str(extension.get("spec_version")) != "1.0":
        _error(errors, path, "ingestion spec requires de_agents.spec_version: '1.0'")
    if status not in INGESTION_SPEC_STATUSES:
        _error(
            errors,
            path,
            f"ingestion spec requires de_agents.spec_status in {sorted(INGESTION_SPEC_STATUSES)}",
        )
    if not _non_empty_string(extension.get("canonical_id")):
        _error(errors, path, "ingestion spec requires de_agents.canonical_id")
    _validate_string_list(
        extension.get("derived_from"),
        path=path,
        field="de_agents.derived_from",
        errors=errors,
        require_non_empty=True,
    )

    ingestion = metadata.get("ingestion")
    if not isinstance(ingestion, dict):
        _error(errors, path, "ingestion must be a mapping")
        return

    gaps = ingestion.get("gaps")
    if not _validate_string_list(
        gaps,
        path=path,
        field="ingestion.gaps",
        errors=errors,
    ):
        gaps = []

    ready = status in READY_STATUSES
    if ready and gaps:
        _error(errors, path, "implementation-ready ingestion specs cannot contain gaps")

    sources = ingestion.get("sources")
    if not isinstance(sources, list) or not sources:
        _error(errors, path, "ingestion.sources must be a non-empty list")
        sources = []
    connection_ids: set[str] = set()
    for index, source in enumerate(sources):
        connection_id = _validate_source(
            source,
            index=index,
            ready=ready,
            path=path,
            errors=errors,
        )
        if connection_id:
            if connection_id in connection_ids:
                _error(errors, path, f"duplicate ingestion source connection_id {connection_id!r}")
            connection_ids.add(connection_id)

    datasets = ingestion.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        _error(errors, path, "ingestion.datasets must be a non-empty list")
        datasets = []
    dataset_keys: set[tuple[str, str, str]] = set()
    for index, dataset in enumerate(datasets):
        key = _validate_dataset(
            dataset,
            index=index,
            connection_ids=connection_ids,
            ready=ready,
            path=path,
            errors=errors,
        )
        if key:
            if key in dataset_keys:
                _error(errors, path, f"duplicate ingestion dataset {'.'.join(key)}")
            dataset_keys.add(key)

    if status in {"approved", "deployed"} and not metadata.get("verified"):
        _error(errors, path, f"{status} ingestion specs require a verified entry")


def export_ingestion_spec(
    concepts: Iterable[Any],
    *,
    canonical_id: str,
    output: Path,
    project_root: Path,
) -> dict[str, Any]:
    """Export one implementation-ready OKF ingestion spec as plain YAML."""
    matching = [
        concept
        for concept in concepts
        if concept.role == "ingestion_spec"
        and concept.metadata.get("de_agents", {}).get("canonical_id") == canonical_id
        and concept.metadata.get("status") != "deprecated"
    ]
    if len(matching) != 1:
        raise DiscoveryError(
            f"Expected one active ingestion_spec with canonical_id {canonical_id!r}; "
            f"found {len(matching)}"
        )
    concept = matching[0]
    errors: list[dict[str, str]] = []
    validate_ingestion_spec(
        concept.metadata,
        path=concept.relative_path.as_posix(),
        errors=errors,
    )
    if errors:
        raise DiscoveryError(f"Ingestion spec validation failed: {errors[0]['message']}")

    status = concept.metadata["de_agents"]["spec_status"]
    if status not in READY_STATUSES:
        raise DiscoveryError(
            "Refusing to export a candidate ingestion spec; resolve its gaps and mark it "
            "implementation-ready first"
        )

    ingestion = concept.metadata["ingestion"]
    projection = {
        "sources": ingestion["sources"],
        "datasets": ingestion["datasets"],
    }
    rendered = yaml.safe_dump(
        projection,
        sort_keys=False,
        allow_unicode=True,
        width=1000,
    )
    findings = scan_text(rendered)
    if findings:
        raise DiscoveryError(
            f"Refusing to export ingestion config containing a potential secret "
            f"({findings[0].detector})"
        )

    resolved_output = ensure_within(output, project_root, "Ingestion config output")
    atomic_write_text(resolved_output, rendered)
    return {
        "exported": True,
        "canonical_id": canonical_id,
        "spec_status": status,
        "source_concept": concept.relative_path.as_posix(),
        "output": str(resolved_output),
        "sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
    }
