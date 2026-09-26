"""Deterministic controls for retained web research evidence."""

from __future__ import annotations

from urllib.parse import urlsplit

from .io import DiscoveryError


def _domain_matches(hostname: str, configured_domain: str) -> bool:
    domain = configured_domain.strip().lower().lstrip(".")
    return bool(domain) and (hostname == domain or hostname.endswith(f".{domain}"))


def validate_web_source(source_uri: str, research_config: dict) -> str:
    if research_config["mode"] == "off":
        raise DiscoveryError("Web observations are disabled by research.mode: off")

    parsed = urlsplit(source_uri)
    if parsed.scheme != "https" or not parsed.hostname:
        raise DiscoveryError("Web observation source URI must be an absolute HTTPS URL")
    if parsed.username or parsed.password:
        raise DiscoveryError("Web observation source URI must not contain embedded credentials")

    hostname = parsed.hostname.lower()
    denied = research_config["denied_domains"]
    if any(_domain_matches(hostname, item) for item in denied):
        raise DiscoveryError(f"Web observation domain is denied by policy: {hostname}")

    allowed = research_config["allowed_domains"]
    if allowed and not any(_domain_matches(hostname, item) for item in allowed):
        raise DiscoveryError(f"Web observation domain is outside the configured allowlist: {hostname}")

    return hostname
