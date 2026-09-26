"""Databricks action classification and deterministic policy gate."""

from __future__ import annotations

import fnmatch
from typing import Any

from .io import DiscoveryError


ACTION_CLASSES: dict[str, set[str]] = {
    "read": {
        "read",
        "list",
        "get",
        "describe",
        "query_metadata",
        "aggregate_profile",
        "inspect_lineage",
    },
    "create_owned": {
        "create_owned",
        "create_connection",
        "create_foreign_catalog",
        "create_external_location",
        "create_lakeflow_connect",
        "create_owned_resource",
    },
    "modify_existing": {
        "modify_existing",
        "alter",
        "update_job",
        "update_pipeline",
        "write_data",
    },
    "manage_permissions": {
        "manage_permissions",
        "grant",
        "revoke",
        "change_owner",
        "create_secret",
    },
    "delete": {"delete", "drop", "purge", "truncate"},
}


def classify_action(action: str) -> str:
    normalized = action.strip().lower()
    for action_class, actions in ACTION_CLASSES.items():
        if normalized in actions:
            return action_class
    raise DiscoveryError(
        f"Unknown action {action!r}; use a class or one of "
        f"{sorted(value for values in ACTION_CLASSES.values() for value in values)}"
    )


def _matches(value: str, patterns: list[str]) -> bool:
    normalized = value.casefold()
    return any(fnmatch.fnmatchcase(normalized, pattern.casefold()) for pattern in patterns)


def authorize(
    config: dict[str, Any],
    *,
    action: str,
    resource_name: str,
    system: str | None,
    catalog: str | None,
    schema: str | None,
) -> dict[str, Any]:
    action_class = classify_action(action)
    policy = config["databricks"]["policy"][action_class]
    reasons: list[str] = []
    boundary_decision = "allow"

    coordinates = {"systems": system, "catalogs": catalog, "schemas": schema}
    if action_class != "create_owned":
        coordinates["assets"] = resource_name
    for dimension, value in coordinates.items():
        if not value:
            continue
        excluded = config["discovery"]["exclude"][dimension]
        included = config["discovery"]["include"][dimension]
        if _matches(value, excluded):
            boundary_decision = "deny"
            reasons.append(f"{dimension[:-1]} {value!r} matches an exclusion")
        elif included and not _matches(value, included):
            if boundary_decision != "deny":
                boundary_decision = "ask"
            reasons.append(f"{dimension[:-1]} {value!r} is outside the include boundary")

    if not any((catalog, schema, resource_name)):
        boundary_decision = "ask"
        reasons.append("No resource coordinates were supplied")

    if action_class == "create_owned":
        prefix = config["databricks"]["agent_resource_prefix"]
        if not resource_name.startswith(prefix):
            boundary_decision = "deny"
            reasons.append(f"Agent-created resources must start with {prefix!r}")

    order = {"allow": 0, "ask": 1, "deny": 2}
    decision = max((policy, boundary_decision), key=order.get)
    if policy != "allow":
        reasons.append(f"Project policy for {action_class} is {policy}")
    if not reasons:
        reasons.append("Action is in boundary and permitted by project policy")
    return {
        "decision": decision.upper(),
        "action": action,
        "action_class": action_class,
        "resource_name": resource_name,
        "system": system,
        "catalog": catalog,
        "schema": schema,
        "reasons": reasons,
    }
