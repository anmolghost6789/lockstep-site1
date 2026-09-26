from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml
from openpyxl import Workbook
from pypdf import PdfWriter


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN_ROOT / "skills" / "discover-project" / "scripts" / "de_discovery.py"


class DiscoveryCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.project = Path(self.tempdir.name)
        self.invoke(
            "init",
            "--project-root",
            str(self.project),
            "--project-id",
            "test-project",
            "--objective",
            "Determine what is needed to deliver trusted order revenue data.",
            "--readiness-target",
            "requirements-ready",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def invoke(self, *arguments: str, expected: int = 0) -> dict:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            cwd=self.project,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != expected:
            self.fail(
                f"Expected exit {expected}, got {result.returncode}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail(f"Command did not return JSON:\n{result.stdout}\n{result.stderr}")

    @property
    def config_path(self) -> Path:
        return self.project / ".de-discovery.yaml"

    def update_config(self, update) -> None:
        value = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        update(value)
        self.config_path.write_text(
            yaml.safe_dump(value, sort_keys=False),
            encoding="utf-8",
        )

    def write_concept(self, relative: str, metadata: dict, body: str) -> Path:
        path = self.project / "knowledge" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        content = (
            "---\n"
            + yaml.safe_dump(metadata, sort_keys=False).strip()
            + "\n---\n\n"
            + body.strip()
            + "\n"
        )
        path.write_text(content, encoding="utf-8")
        return path

    @staticmethod
    def generated() -> dict:
        return {"by": "de-discovery/0.3.0", "at": "2026-07-27T10:00:00Z"}

    @staticmethod
    def complete_sections(names: list[str]) -> dict:
        return {
            name: {"status": "supported", "gaps": []}
            for name in names
        }

    def write_structured_concept(
        self,
        *,
        relative: str,
        role: str,
        field: str,
        sections: list[str],
        extension: dict | None = None,
    ) -> Path:
        de_agents = {
            "canonical_id": f"{role}.{Path(relative).stem}",
            "role": role,
            "observation": "inferred",
            "source_revision_ids": [],
        }
        de_agents.update(extension or {})
        return self.write_concept(
            relative,
            {
                "type": role.replace("_", "-"),
                "title": role.replace("_", " ").title(),
                "status": "draft",
                "sources": [],
                "generated": self.generated(),
                "de_agents": de_agents,
                field: self.complete_sections(sections),
            },
            f"Structured {role} handoff.",
        )

    def append_manifest_links(
        self,
        links: list[tuple[str, str]],
        *,
        routes: dict[str, list[str]] | None = None,
    ) -> None:
        path = self.project / "knowledge" / "handoff" / "agent-entrypoint.md"
        lines = [f"- [{label}]({target})" for label, target in links]
        content = path.read_text(encoding="utf-8")
        if routes:
            _, frontmatter, body = content.split("---", 2)
            metadata = yaml.safe_load(frontmatter)
            downstream = metadata["de_agents"]["downstream_context"]
            for agent, canonical_ids in routes.items():
                downstream[agent].extend(canonical_ids)
            content = (
                "---\n"
                + yaml.safe_dump(metadata, sort_keys=False).strip()
                + "\n---"
                + body
            )
        path.write_text(content + "\n" + "\n".join(lines) + "\n", encoding="utf-8")

    def write_ingestion_spec(
        self,
        *,
        relative: str = "acquisition/orders-ingestion.md",
        canonical_id: str = "ingestion.orders.current",
        derived_from: str = "acquisition_contract.orders-feed",
        status: str = "candidate",
        ready: bool = False,
    ) -> Path:
        dataset = {
            "connection_id": "commercial_postgres_main",
            "source_schema": "sales",
            "source_table": "orders",
            "destination_table": "raw_orders",
            "load_type": "incremental",
            "watermark_column": "updated_at",
        }
        if ready:
            dataset.update(
                {
                    "destination_catalog": "${var.destination_catalog}",
                    "destination_schema": "${var.destination_schema}",
                    "primary_keys": ["order_id"],
                    "watermark_validation": {"status": "supported", "gaps": []},
                    "schedule": {"mode": "periodic", "interval": 1, "unit": "hours"},
                    "delete_handling": {
                        "mode": "soft",
                        "condition": "deleted_at IS NOT NULL",
                    },
                    "schema_evolution": {"mode": "add_new_columns"},
                    "reconciliation": {
                        "checks": ["row_count", "sum_order_amount"],
                        "owner": "Commercial data owner",
                    },
                    "recovery": {
                        "checkpoint_or_state": "Lakeflow-managed ingestion state",
                        "replay_strategy": "Reset and replay the approved source window",
                    },
                }
            )
        return self.write_concept(
            relative,
            {
                "type": "ingestion-spec",
                "title": "Orders ingestion specification",
                "status": "draft",
                "sources": [],
                "generated": self.generated(),
                "de_agents": {
                    "canonical_id": canonical_id,
                    "role": "ingestion_spec",
                    "observation": "proposed",
                    "source_revision_ids": [],
                    "spec_version": "1.0",
                    "spec_status": status,
                    "derived_from": [derived_from],
                },
                "ingestion": {
                    "gaps": [] if ready else ["Primary key and operational controls need evidence."],
                    "sources": [
                        {
                            "connection_id": "commercial_postgres_main",
                            "source_type": "rdbms",
                            "engine": "postgresql",
                            "host": "${var.pg_host}",
                            "port": 5432,
                            "database": "commercial_db",
                            "connection_name": "${var.connection_name}",
                            "secret_reference": "commercial-postgres-creds",
                        }
                    ],
                    "datasets": [dataset],
                },
            },
            "Machine-readable ingestion handoff derived from the acquisition contract.",
        )

    def write_test_acquisition_contract(
        self,
        *,
        relative: str = "acquisition/orders-feed.md",
    ) -> Path:
        return self.write_structured_concept(
            relative=relative,
            role="acquisition_contract",
            field="acquisition",
            sections=[
                "source_scope",
                "target_mapping",
                "delivery",
                "change_capture",
                "schema",
                "quality_reconciliation",
                "security_governance",
                "operations_recovery",
            ],
            extension={"contract_version": "1.0", "contract_status": "feasible"},
        )

    def ingest_source(self) -> tuple[str, str]:
        source = self.project / "inputs" / "charter.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(
            "# Charter\n\nBuild governed order revenue data for finance.\n",
            encoding="utf-8",
        )
        result = self.invoke(
            "ingest",
            "--project-root",
            str(self.project),
            "--path",
            str(source),
        )
        item = result["results"][0]
        return item["revision_id"], item["resource"]

    def create_valid_profile(
        self,
        *,
        archetypes: list[str] | None = None,
        facets: list[str] | None = None,
        readiness_target: str = "requirements-ready",
    ) -> tuple[str, str]:
        archetypes = archetypes or ["general"]
        facets = facets or [
            "business",
            "data",
            "governance",
            "landscape",
            "operations",
            "quality",
        ]
        revision_id, resource = self.ingest_source()
        common_source = [
            {
                "id": revision_id,
                "resource": resource,
                "description": "Project charter",
            }
        ]
        self.write_concept(
            "maps/current-boundary.md",
            {
                "type": "bounded-investigation",
                "title": "Current discovery boundary",
                "status": "draft",
                "sources": common_source,
                "generated": self.generated(),
                "de_agents": {
                    "canonical_id": "discovery.boundary.current",
                    "role": "discovery_boundary",
                    "observation": "reported",
                    "boundary_status": "active",
                    "source_revision_ids": [revision_id],
                },
            },
            (
                "Included: the order-revenue initiative.[^"
                + revision_id
                + "]\n\n"
                "Excluded: unrelated enterprise catalogs.\n\n"
                f"[^{revision_id}]: Project charter."
            ),
        )
        (self.project / "knowledge" / "log.md").write_text(
            "# Knowledge log\n\n"
            "## 2026-07-27\n\n"
            "- Registered the charter and created the initial bounded handoff.\n",
            encoding="utf-8",
        )
        self.invoke(
            "review-source",
            "--project-root",
            str(self.project),
            "--revision-id",
            revision_id,
            "--disposition",
            "applied",
            "--concept",
            "context.order-revenue.current",
            "--concept",
            "discovery.boundary.current",
            "--concept",
            "readiness.requirements.current",
            "--reason",
            "Charter claims were incorporated into the current discovery concepts.",
        )
        self.write_concept(
            "gates/requirements-check.md",
            {
                "type": "readiness-evaluation",
                "title": "Requirements readiness",
                "status": "draft",
                "sources": common_source,
                "generated": self.generated(),
                "de_agents": {
                    "canonical_id": "readiness.requirements.current",
                    "role": "readiness_assessment",
                    "observation": "inferred",
                    "readiness_target": readiness_target,
                    "readiness_result": "conditional",
                    "source_revision_ids": [revision_id],
                },
            },
            "The objective is evidenced; acceptance ownership remains assigned.",
        )
        self.write_concept(
            "handoff/agent-entrypoint.md",
            {
                "type": "agent-context-manifest",
                "title": "Order revenue context",
                "status": "draft",
                "sources": common_source,
                "generated": self.generated(),
                "de_agents": {
                    "canonical_id": "context.order-revenue.current",
                    "role": "context_manifest",
                    "observation": "inferred",
                    "readiness_target": readiness_target,
                    "engagement_archetypes": archetypes,
                    "required_facets": facets,
                    "facet_coverage": {
                        facet: "supported" if facet == "business" else "partial"
                        for facet in facets
                    },
                    "downstream_context": {
                        "requirements": [
                            "discovery.boundary.current",
                            "readiness.requirements.current",
                        ],
                        "design": [
                            "discovery.boundary.current",
                            "readiness.requirements.current",
                        ],
                        "build": [
                            "discovery.boundary.current",
                            "readiness.requirements.current",
                        ],
                    },
                    "source_revision_ids": [revision_id],
                },
            },
            (
                "Start with the [boundary](/maps/current-boundary.md) and "
                "[readiness assessment](/gates/requirements-check.md)."
            ),
        )
        return revision_id, resource

    def test_ingest_is_content_addressed_and_incremental(self) -> None:
        source = self.project / "charter.md"
        source.write_text("Initial objective", encoding="utf-8")
        first = self.invoke(
            "ingest", "--project-root", str(self.project), "--path", str(source)
        )
        second = self.invoke(
            "ingest", "--project-root", str(self.project), "--path", str(source)
        )
        source.write_text("Revised objective", encoding="utf-8")
        third = self.invoke(
            "ingest", "--project-root", str(self.project), "--path", str(source)
        )

        self.assertEqual(first["new"], 1)
        self.assertEqual(second["unchanged"], 1)
        self.assertEqual(third["changed"], 1)
        self.assertNotEqual(
            first["results"][0]["revision_id"],
            third["results"][0]["revision_id"],
        )
        state = yaml.safe_load(
            (self.project / ".de-discovery" / "state.yaml").read_text(encoding="utf-8")
        )
        registry = next(iter(state["sources"].values()))
        self.assertEqual(len(registry["revisions"]), 2)
        self.assertTrue(
            (
                self.project
                / ".de-discovery"
                / "evidence"
                / "sha256"
                / first["results"][0]["sha256"]
                / "charter.md"
            ).is_file()
        )

    def test_secret_evidence_is_refused_without_state_leak(self) -> None:
        secret = self.project / "secret.txt"
        secret.write_text("password = definitely-a-real-secret-value", encoding="utf-8")
        result = self.invoke(
            "ingest",
            "--project-root",
            str(self.project),
            "--path",
            str(secret),
            expected=1,
        )
        self.assertEqual(result["ingested"], 0)
        self.assertIn("Potential secret", result["failures"][0]["error"])
        state = yaml.safe_load(
            (self.project / ".de-discovery" / "state.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(state["sources"], {})

    def test_office_pdf_and_spreadsheet_inputs_are_extracted(self) -> None:
        inputs = self.project / "mixed-inputs"
        inputs.mkdir()
        with zipfile.ZipFile(inputs / "meeting.docx", "w") as archive:
            archive.writestr(
                "word/document.xml",
                "<document><body><p><t>Finance needs trusted net revenue.</t></p></body></document>",
            )
        with zipfile.ZipFile(inputs / "architecture.pptx", "w") as archive:
            archive.writestr(
                "ppt/slides/slide2.xml",
                "<slide><t>Orders curated table</t></slide>",
            )
            archive.writestr(
                "ppt/slides/slide10.xml",
                "<slide><t>Finance dashboard</t></slide>",
            )
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Data Contract"
        worksheet.append(["field", "meaning"])
        worksheet.append(["order_id", "Stable order identifier"])
        workbook.save(inputs / "contract.xlsx")
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        with (inputs / "legacy.pdf").open("wb") as handle:
            writer.write(handle)

        result = self.invoke(
            "ingest",
            "--project-root",
            str(self.project),
            "--path",
            str(inputs),
        )
        self.assertEqual(result["ingested"], 4)
        self.assertEqual(result["failures"], [])
        derived = self.project / ".de-discovery" / "evidence" / "derived"
        extracted = "\n".join(
            path.read_text(encoding="utf-8") for path in derived.glob("*.md")
        )
        self.assertIn("Finance needs trusted net revenue.", extracted)
        self.assertLess(
            extracted.index("Orders curated table"),
            extracted.index("Finance dashboard"),
        )
        self.assertIn("Stable order identifier", extracted)

    def test_databricks_observation_keeps_provider_provenance(self) -> None:
        note = self.project / "inputs" / "observations" / "orders-profile.md"
        note.parent.mkdir(parents=True)
        note.write_text(
            "# Aggregate profile\n\n"
            "Observed through AI Dev Kit MCP at 2026-07-27T10:00:00Z.\n"
            "The bounded aggregate reported 1,000 rows and no sampled values.\n",
            encoding="utf-8",
        )
        result = self.invoke(
            "register-observation",
            "--project-root",
            str(self.project),
            "--kind",
            "databricks",
            "--title",
            "Orders aggregate profile",
            "--source-uri",
            "databricks://workspace/catalog/sales/schema/bronze/table/orders?observed_at=2026-07-27T10:00:00Z",
            "--content-file",
            str(note),
        )
        revision_id = result["observation"]["revision_id"]
        state = yaml.safe_load(
            (self.project / ".de-discovery" / "state.yaml").read_text(encoding="utf-8")
        )
        revision = next(
            revision
            for source in state["sources"].values()
            for revision in source["revisions"]
            if revision["id"] == revision_id
        )
        self.assertEqual(revision["observation_kind"], "databricks")
        self.assertEqual(revision["observation_title"], "Orders aggregate profile")
        self.assertTrue(revision["source_uri"].startswith("databricks://"))

    def test_web_observation_enforces_research_policy_and_provenance(self) -> None:
        def update(value):
            value["research"]["mode"] = "official-only"
            value["research"]["allowed_domains"] = ["docs.databricks.com"]

        self.update_config(update)
        note = self.project / "inputs" / "observations" / "connector-guidance.md"
        note.parent.mkdir(parents=True)
        note.write_text(
            "# Connector guidance\n\n"
            "Question: Which cursor constraints affect this proposed feed?\n"
            "Claim: A single monotonic cursor is required for this connector.\n",
            encoding="utf-8",
        )
        missing_provenance = self.invoke(
            "register-observation",
            "--project-root",
            str(self.project),
            "--kind",
            "web",
            "--title",
            "Query connector guidance",
            "--source-uri",
            "https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/query-based-reference",
            "--content-file",
            str(note),
            expected=1,
        )
        self.assertIn("publisher", missing_provenance["error"])

        accepted = self.invoke(
            "register-observation",
            "--project-root",
            str(self.project),
            "--kind",
            "web",
            "--title",
            "Query connector guidance",
            "--source-uri",
            "https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/query-based-reference",
            "--publisher",
            "Databricks",
            "--applicability",
            "AWS; query-based connectors; design feasibility",
            "--content-file",
            str(note),
        )
        blocked = self.invoke(
            "register-observation",
            "--project-root",
            str(self.project),
            "--kind",
            "web",
            "--title",
            "Unapproved source",
            "--source-uri",
            "https://example.test/advice",
            "--publisher",
            "Example",
            "--applicability",
            "Unverified",
            "--content-file",
            str(note),
            expected=1,
        )
        self.assertTrue(accepted["registered"])
        self.assertIn("allowlist", blocked["error"])
        state = yaml.safe_load(
            (self.project / ".de-discovery" / "state.yaml").read_text(encoding="utf-8")
        )
        revision = next(
            revision
            for source in state["sources"].values()
            for revision in source["revisions"]
            if revision["id"] == accepted["observation"]["revision_id"]
        )
        self.assertEqual(revision["publisher"], "Databricks")
        self.assertEqual(revision["source_domain"], "docs.databricks.com")
        self.assertIn("query-based connectors", revision["applicability"])

    def test_acquisition_facet_requires_structured_contracts_and_manifest_links(self) -> None:
        facets = [
            "acquisition",
            "business",
            "data",
            "governance",
            "landscape",
            "operations",
            "platform",
            "quality",
        ]

        def update(value):
            value["engagement"]["archetypes"] = ["source-onboarding"]

        self.update_config(update)
        self.create_valid_profile(archetypes=["source-onboarding"], facets=facets)
        missing = self.invoke(
            "validate",
            "--project-root",
            str(self.project),
            "--profile",
            expected=1,
        )
        self.assertTrue(
            any("source_system_profile" in item["message"] for item in missing["errors"])
        )
        self.assertTrue(
            any("acquisition_contract" in item["message"] for item in missing["errors"])
        )
        self.assertTrue(
            any("ingestion_spec" in item["message"] for item in missing["errors"])
        )

        self.write_structured_concept(
            relative="acquisition/source-sales.md",
            role="source_system_profile",
            field="source_system",
            sections=[
                "identity_ownership",
                "connectivity_access",
                "structure_scale",
                "change_capabilities",
                "security_governance",
                "operational_constraints",
            ],
        )
        self.write_structured_concept(
            relative="acquisition/orders-feed.md",
            role="acquisition_contract",
            field="acquisition",
            sections=[
                "source_scope",
                "target_mapping",
                "delivery",
                "change_capture",
                "schema",
                "quality_reconciliation",
                "security_governance",
                "operations_recovery",
            ],
            extension={"contract_version": "1.0", "contract_status": "feasible"},
        )
        self.write_ingestion_spec()
        self.append_manifest_links(
            [
                ("Sales source", "/acquisition/source-sales.md"),
                ("Orders acquisition", "/acquisition/orders-feed.md"),
                ("Orders ingestion", "/acquisition/orders-ingestion.md"),
            ],
            routes={
                "design": ["ingestion.orders.current"],
                "build": ["ingestion.orders.current"],
            },
        )
        report = self.invoke(
            "validate", "--project-root", str(self.project), "--profile"
        )
        self.assertTrue(report["valid"])

    def test_ingestion_spec_must_be_routed_to_design_and_build(self) -> None:
        facets = [
            "acquisition",
            "business",
            "data",
            "governance",
            "landscape",
            "operations",
            "platform",
            "quality",
        ]

        def update(value):
            value["engagement"]["archetypes"] = ["source-onboarding"]

        self.update_config(update)
        self.create_valid_profile(archetypes=["source-onboarding"], facets=facets)
        self.write_structured_concept(
            relative="acquisition/source-sales.md",
            role="source_system_profile",
            field="source_system",
            sections=[
                "identity_ownership",
                "connectivity_access",
                "structure_scale",
                "change_capabilities",
                "security_governance",
                "operational_constraints",
            ],
        )
        self.write_structured_concept(
            relative="acquisition/orders-feed.md",
            role="acquisition_contract",
            field="acquisition",
            sections=[
                "source_scope",
                "target_mapping",
                "delivery",
                "change_capture",
                "schema",
                "quality_reconciliation",
                "security_governance",
                "operations_recovery",
            ],
            extension={"contract_version": "1.0", "contract_status": "feasible"},
        )
        self.write_ingestion_spec()
        self.append_manifest_links(
            [
                ("Sales source", "/acquisition/source-sales.md"),
                ("Orders acquisition", "/acquisition/orders-feed.md"),
                ("Orders ingestion", "/acquisition/orders-ingestion.md"),
            ]
        )
        missing_route = self.invoke(
            "validate",
            "--project-root",
            str(self.project),
            "--profile",
            expected=1,
        )
        messages = [item["message"] for item in missing_route["errors"]]
        self.assertTrue(any("downstream_context.design" in item for item in messages))
        self.assertTrue(any("downstream_context.build" in item for item in messages))

    def test_candidate_ingestion_spec_cannot_be_exported(self) -> None:
        self.write_test_acquisition_contract()
        self.write_ingestion_spec()
        validation = self.invoke("validate", "--project-root", str(self.project))
        rejected = self.invoke(
            "export-ingestion-config",
            "--project-root",
            str(self.project),
            "--canonical-id",
            "ingestion.orders.current",
            expected=1,
        )
        self.assertTrue(validation["valid"])
        self.assertIn("candidate ingestion spec", rejected["error"])

    def test_implementation_ready_ingestion_spec_exports_plain_yaml(self) -> None:
        self.write_test_acquisition_contract()
        self.write_ingestion_spec(status="implementation-ready", ready=True)
        result = self.invoke(
            "export-ingestion-config",
            "--project-root",
            str(self.project),
            "--canonical-id",
            "ingestion.orders.current",
        )
        output = yaml.safe_load(Path(result["output"]).read_text(encoding="utf-8"))
        self.assertEqual(set(output), {"sources", "datasets"})
        self.assertEqual(
            output["datasets"][0]["watermark_column"],
            "updated_at",
        )
        self.assertEqual(
            output["datasets"][0]["primary_keys"],
            ["order_id"],
        )

    def test_implementation_ready_incremental_spec_requires_controls(self) -> None:
        self.write_test_acquisition_contract()
        path = self.write_ingestion_spec(status="implementation-ready", ready=True)
        content = path.read_text(encoding="utf-8")
        _, frontmatter, body = content.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        dataset = metadata["ingestion"]["datasets"][0]
        del dataset["watermark_validation"]
        del dataset["recovery"]
        path.write_text(
            "---\n"
            + yaml.safe_dump(metadata, sort_keys=False).strip()
            + "\n---"
            + body,
            encoding="utf-8",
        )
        report = self.invoke(
            "validate",
            "--project-root",
            str(self.project),
            expected=1,
        )
        messages = [item["message"] for item in report["errors"]]
        self.assertTrue(any("watermark_validation.status" in item for item in messages))
        self.assertTrue(any(".recovery must be a mapping" in item for item in messages))

    def test_implementation_ready_file_spec_uses_feed_identity_not_table_fields(self) -> None:
        self.write_test_acquisition_contract()
        path = self.write_ingestion_spec(status="implementation-ready", ready=True)
        content = path.read_text(encoding="utf-8")
        _, frontmatter, body = content.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        source = metadata["ingestion"]["sources"][0]
        source["source_type"] = "object_storage"
        source.pop("engine")
        source.pop("database")
        dataset = metadata["ingestion"]["datasets"][0]
        dataset.update(
            {
                "asset_type": "file",
                "source_uri": "s3://commercial-drop/prescriptions/",
                "file_format": "json",
            }
        )
        for field in (
            "source_schema",
            "source_table",
            "watermark_column",
            "watermark_validation",
            "primary_keys",
        ):
            dataset.pop(field)
        path.write_text(
            "---\n"
            + yaml.safe_dump(metadata, sort_keys=False).strip()
            + "\n---"
            + body,
            encoding="utf-8",
        )
        report = self.invoke("validate", "--project-root", str(self.project))
        self.assertTrue(report["valid"])

    def test_incomplete_acquisition_contract_is_rejected(self) -> None:
        facets = [
            "acquisition",
            "business",
            "data",
            "governance",
            "landscape",
            "operations",
            "platform",
            "quality",
        ]

        def update(value):
            value["engagement"]["archetypes"] = ["source-onboarding"]

        self.update_config(update)
        self.create_valid_profile(archetypes=["source-onboarding"], facets=facets)
        self.write_structured_concept(
            relative="acquisition/source-sales.md",
            role="source_system_profile",
            field="source_system",
            sections=[
                "identity_ownership",
                "connectivity_access",
                "structure_scale",
                "change_capabilities",
                "security_governance",
                "operational_constraints",
            ],
        )
        self.write_structured_concept(
            relative="acquisition/orders-feed.md",
            role="acquisition_contract",
            field="acquisition",
            sections=[
                "source_scope",
                "target_mapping",
                "delivery",
                "schema",
                "quality_reconciliation",
                "security_governance",
                "operations_recovery",
            ],
            extension={"contract_version": "1.0", "contract_status": "assessed"},
        )
        self.append_manifest_links(
            [
                ("Sales source", "/acquisition/source-sales.md"),
                ("Orders acquisition", "/acquisition/orders-feed.md"),
            ]
        )
        report = self.invoke(
            "validate",
            "--project-root",
            str(self.project),
            "--profile",
            expected=1,
        )
        self.assertTrue(
            any(
                "missing required sections" in item["message"]
                and "change_capture" in item["message"]
                for item in report["errors"]
            )
        )

    def test_design_ready_migration_profile_requires_units_plan_and_acquisition(self) -> None:
        archetypes = ["migration-modernization", "source-onboarding"]
        facets = [
            "acquisition",
            "business",
            "change",
            "consumption",
            "data",
            "economics",
            "governance",
            "landscape",
            "operations",
            "platform",
            "processing",
            "quality",
        ]

        def update(value):
            value["readiness_target"] = "design-ready"
            value["engagement"]["archetypes"] = archetypes

        self.update_config(update)
        self.create_valid_profile(
            archetypes=archetypes,
            facets=facets,
            readiness_target="design-ready",
        )
        concepts = [
            (
                "acquisition/source-legacy.md",
                "source_system_profile",
                "source_system",
                [
                    "identity_ownership",
                    "connectivity_access",
                    "structure_scale",
                    "change_capabilities",
                    "security_governance",
                    "operational_constraints",
                ],
                {},
            ),
            (
                "acquisition/legacy-orders.md",
                "acquisition_contract",
                "acquisition",
                [
                    "source_scope",
                    "target_mapping",
                    "delivery",
                    "change_capture",
                    "schema",
                    "quality_reconciliation",
                    "security_governance",
                    "operations_recovery",
                ],
                {"contract_version": "1.0", "contract_status": "feasible"},
            ),
            (
                "migration/assessment.md",
                "migration_assessment",
                "migration_assessment",
                [
                    "drivers_scope",
                    "estate_inventory",
                    "dependencies",
                    "usage_disposition",
                    "compatibility",
                    "target_mapping",
                    "economics",
                    "risks_assumptions",
                ],
                {},
            ),
            (
                "migration/order-reporting.md",
                "migration_unit",
                "migration_unit",
                [
                    "scope",
                    "dependencies",
                    "disposition",
                    "data",
                    "code",
                    "consumers",
                    "validation",
                    "cutover_rollback",
                ],
                {
                    "migration_disposition": "convert",
                    "migration_complexity": "high",
                },
            ),
            (
                "migration/plan.md",
                "migration_plan",
                "migration_plan",
                [
                    "waves",
                    "sequencing",
                    "coexistence",
                    "validation",
                    "cutover_rollback",
                    "decommission",
                ],
                {},
            ),
        ]
        links: list[tuple[str, str]] = []
        for relative, role, field, sections, extension in concepts:
            self.write_structured_concept(
                relative=relative,
                role=role,
                field=field,
                sections=sections,
                extension=extension,
            )
            links.append((role, f"/{relative}"))
        self.write_ingestion_spec(
            relative="acquisition/legacy-orders-ingestion.md",
            canonical_id="ingestion.legacy-orders.current",
            derived_from="acquisition_contract.legacy-orders",
            status="implementation-ready",
            ready=True,
        )
        links.append(
            ("ingestion_spec", "/acquisition/legacy-orders-ingestion.md")
        )
        self.append_manifest_links(
            links,
            routes={
                "design": ["ingestion.legacy-orders.current"],
                "build": ["ingestion.legacy-orders.current"],
            },
        )
        report = self.invoke(
            "validate", "--project-root", str(self.project), "--profile"
        )
        self.assertTrue(report["valid"])

    def test_status_detects_unregistered_source_change(self) -> None:
        source = self.project / "source.sql"
        source.write_text("select 1", encoding="utf-8")
        self.invoke("ingest", "--project-root", str(self.project), "--path", str(source))
        source.write_text("select 2", encoding="utf-8")
        status = self.invoke("status", "--project-root", str(self.project))
        self.assertEqual(len(status["changed_sources"]), 1)
        self.assertEqual(status["changed_sources"][0]["path"], str(source))

    def test_changed_evidence_reopens_completion_and_reports_impacted_concepts(self) -> None:
        self.create_valid_profile()
        self.invoke("rebuild-index", "--project-root", str(self.project))
        self.invoke(
            "set-phase",
            "--project-root",
            str(self.project),
            "--phase",
            "complete",
        )
        charter = self.project / "inputs" / "charter.md"
        charter.write_text(
            "# Charter\n\nBuild governed order net revenue data for finance.\n",
            encoding="utf-8",
        )
        result = self.invoke(
            "ingest",
            "--project-root",
            str(self.project),
            "--path",
            str(charter),
        )
        impacted = {item["canonical_id"] for item in result["results"][0]["impacted_concepts"]}
        status = self.invoke("status", "--project-root", str(self.project))
        self.assertEqual(result["changed"], 1)
        self.assertEqual(
            impacted,
            {
                "context.order-revenue.current",
                "discovery.boundary.current",
                "readiness.requirements.current",
            },
        )
        self.assertEqual(status["phase"], "discover")
        self.assertEqual(len(status["pending_source_revisions"]), 1)

    def test_databricks_policy_enforces_boundary_prefix_and_delete_denial(self) -> None:
        def update(value):
            value["discovery"]["include"]["catalogs"] = ["sales"]
            value["discovery"]["include"]["schemas"] = ["bronze*"]
            value["discovery"]["include"]["assets"] = ["orders*"]

        self.update_config(update)
        allowed = self.invoke(
            "authorize-action",
            "--project-root",
            str(self.project),
            "--action",
            "query_metadata",
            "--resource-name",
            "orders",
            "--catalog",
            "sales",
            "--schema",
            "bronze_orders",
        )
        outside = self.invoke(
            "authorize-action",
            "--project-root",
            str(self.project),
            "--action",
            "query_metadata",
            "--resource-name",
            "orders",
            "--catalog",
            "finance",
            "--schema",
            "bronze_orders",
            expected=2,
        )
        bad_prefix = self.invoke(
            "authorize-action",
            "--project-root",
            str(self.project),
            "--action",
            "create_connection",
            "--resource-name",
            "source_connection",
            "--catalog",
            "sales",
            "--schema",
            "bronze_orders",
            expected=3,
        )
        denied = self.invoke(
            "authorize-action",
            "--project-root",
            str(self.project),
            "--action",
            "drop",
            "--resource-name",
            "orders",
            "--catalog",
            "sales",
            "--schema",
            "bronze_orders",
            expected=3,
        )
        self.assertEqual(allowed["decision"], "ALLOW")
        self.assertEqual(outside["decision"], "ASK")
        self.assertEqual(bad_prefix["decision"], "DENY")
        self.assertEqual(denied["decision"], "DENY")

    def test_dynamic_okf_profile_validates_and_allows_completion(self) -> None:
        self.create_valid_profile()
        rebuilt = self.invoke("rebuild-index", "--project-root", str(self.project))
        validation = self.invoke(
            "validate", "--project-root", str(self.project), "--profile"
        )
        completed = self.invoke(
            "set-phase",
            "--project-root",
            str(self.project),
            "--phase",
            "complete",
            "--last-step",
            "Validated OKF handoff",
        )
        self.assertTrue(rebuilt["rebuilt"])
        self.assertTrue(validation["valid"])
        self.assertEqual(validation["readiness_result"], "conditional")
        self.assertEqual(completed["phase"], "complete")
        index = (self.project / "knowledge" / "index.md").read_text(encoding="utf-8")
        self.assertIn("/handoff/agent-entrypoint.md", index)
        self.assertIn("/maps/current-boundary.md", index)

    def test_completion_rejects_open_blocking_question(self) -> None:
        self.create_valid_profile()
        self.invoke("rebuild-index", "--project-root", str(self.project))
        self.invoke(
            "record-question",
            "--project-root",
            str(self.project),
            "--id",
            "owner-acceptance",
            "--question",
            "Who owns acceptance criteria?",
        )
        failed = self.invoke(
            "set-phase",
            "--project-root",
            str(self.project),
            "--phase",
            "complete",
            expected=1,
        )
        self.assertIn("open blocking", failed["error"])

    def test_context_manifest_must_declare_created_resources(self) -> None:
        self.create_valid_profile()
        self.invoke(
            "record-resource",
            "--project-root",
            str(self.project),
            "--type",
            "connection",
            "--name",
            "de_discovery_orders",
            "--purpose",
            "Read-only source metadata discovery",
        )
        report = self.invoke(
            "validate",
            "--project-root",
            str(self.project),
            "--profile",
            expected=1,
        )
        self.assertTrue(
            any("created resource" in item["message"] for item in report["errors"])
        )

    def test_claim_citation_requires_matching_source(self) -> None:
        self.create_valid_profile()
        path = self.project / "knowledge" / "maps" / "current-boundary.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "Excluded: unrelated enterprise catalogs.",
                "Excluded: unrelated enterprise catalogs.[^missing-source]",
            ),
            encoding="utf-8",
        )
        report = self.invoke(
            "validate",
            "--project-root",
            str(self.project),
            "--profile",
            expected=1,
        )
        self.assertTrue(
            any("missing-source" in item["message"] for item in report["errors"])
        )

    def test_candidate_scoring_retains_components_and_flags_blocking_risk(self) -> None:
        candidates = self.project / "candidates.yaml"
        candidates.write_text(
            yaml.safe_dump(
                {
                    "candidates": [
                        {
                            "name": "orders_curated",
                            "scores": {
                                "objective_relevance": 5,
                                "seed_proximity": 4,
                                "authoritative_use": 3,
                                "structural_fit": 3,
                                "operational_fitness": 2,
                                "evidence_risk": -1,
                            },
                            "reasons": {
                                "objective_relevance": "Named in charter",
                                "seed_proximity": "Direct seed",
                                "authoritative_use": "Finance-owned",
                                "structural_fit": "Order grain",
                                "operational_fitness": "Current",
                                "evidence_risk": "One open quality issue",
                            },
                        },
                        {
                            "name": "orders_legacy",
                            "scores": {
                                "objective_relevance": 5,
                                "seed_proximity": 3,
                                "authoritative_use": 1,
                                "structural_fit": 3,
                                "operational_fitness": 0,
                                "evidence_risk": -5,
                            },
                            "reasons": {
                                "objective_relevance": "Matching fields",
                                "seed_proximity": "One hop",
                                "authoritative_use": "Unknown owner",
                                "structural_fit": "Order grain",
                                "operational_fitness": "Stale",
                                "evidence_risk": "Contradicted and stale",
                            },
                        },
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        result = self.invoke("score-candidates", "--input", str(candidates))
        self.assertEqual(result["candidates"][0]["name"], "orders_curated")
        self.assertTrue(result["candidates"][1]["blocking_risk"])

    def test_knowledge_root_cannot_escape_project(self) -> None:
        config = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        config["knowledge_root"] = "../outside"
        self.config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
        result = self.invoke(
            "status",
            "--project-root",
            str(self.project),
            expected=1,
        )
        self.assertIn("within project root", result["error"])

    def test_config_and_resource_uri_refuse_credentials(self) -> None:
        config = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        config["source_password"] = "definitely-a-real-secret-value"
        self.config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
        config_error = self.invoke(
            "status",
            "--project-root",
            str(self.project),
            expected=1,
        )
        self.assertIn("Potential secret detected in config", config_error["error"])

        del config["source_password"]
        self.config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
        uri_error = self.invoke(
            "record-resource",
            "--project-root",
            str(self.project),
            "--type",
            "connection",
            "--name",
            "de_discovery_orders",
            "--uri",
            "https://user:password@example.test/connection",
            "--purpose",
            "Metadata discovery",
            expected=1,
        )
        self.assertIn("embedded credentials", uri_error["error"])


if __name__ == "__main__":
    unittest.main()
