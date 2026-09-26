# Enterprise Readiness

What changes when this package moves from one engineer's laptop to a regulated enterprise, and where each control lives.

> **Gate modes.** By default (`gate_mode: github`) each gate is a pull request reviewed by the CODEOWNERS team for that phase and enforced by branch protection, so approval identity, separation of duties and version binding come from GitHub. The script-based controls described below (`adlc_gate.py`, `adlc/.gates/`) are the **local** mode, for environments without GitHub, and the reference implementation of the same rules.

## 1. What the reference package already gets right

The Design Agent package this is modelled on has a strong base, and ADLC keeps all of it:

| Pattern | Where it lives here |
|---|---|
| Hidden shared-protocol skill plus self-contained phase skills | `.claude/skills/adlc/SKILL.md` and one folder per phase |
| Contracts in `specs/`, templates, deterministic scripts | `.claude/skills/adlc/specs`, `templates`, `scripts` |
| Idempotent re-entry for every phase | "Idempotent re-entry" section in each SKILL.md |
| Thresholded subagents, orchestrator owns humans | `.claude/agents/`, `utilities/subagent-orchestration.md` |
| Context tiers and precedence | `context/guidance/*`, CLAUDE.md principle 7 |
| Governed memory with promotion rules | `memory/` |
| Bounded bookkeeping and progress projection | `scripts/state.py` → `progress.json` |
| Chat discipline and single-statement facts | CLAUDE.md principles 10 and 12 |

## 2. What an enterprise security review adds

| Question the client will ask | Reference package | ADLC enterprise package |
|---|---|---|
| Who approved this, and were they allowed to? | Invoking the next command counts as approval | Named-role gates: `adlc_gate.py` resolves identity (SSO via the extension, or git) and roles (IdP groups), and refuses anyone without the role |
| Can the author approve their own work? | Not addressed | Separation of duties enforced in code |
| What exact version was approved? | Not recorded | Approval binds to the artifact's sha256; any later edit invalidates the gate |
| Can the log be tampered with? | Interaction log in state | Hash-chained, append-only audit log with `verify` and CSV export |
| Can the agent bypass a gate by editing files? | No guard | Pre-tool hook plus permission deny rules block writes to gate and audit folders |
| Which tools and models can it use? | `.mcp.json` lists servers | MCP allow-list per server, tool and phase, enforced on every call; approved-model list checked at phase 2 |
| Where do model calls go? | Direct | Gateway required via managed settings (`ANTHROPIC_BASE_URL`), telemetry off |
| How is sensitive data handled? | Memory excludes PII | Classification levels, pointer-only handling above `internal`, PII and secret scans before each gate |
| What stops a bad release? | Evaluator recommendation | Independent evaluator, thresholds only from the approved AIPRS, risk-based extra approvers at G5, and the deploy job fails closed on `adlc_gate.py check --gate G5` |
| Can users loosen the rules? | Project settings | `managed-settings.example.json` deployed through MDM, bypass mode disabled |

## 3. Control map

| Control | Mechanism | Evidence for auditors |
|---|---|---|
| Access control and RBAC | `config/governance/gate_roles.json`, IdP group mapping | Gate files list approver identity and role |
| Segregation of duties | `adlc_gate.py` rejects requester = approver | `gate.denied` events |
| Change management | Six gates bound to artifact hashes; per-diff review at G3 | `adlc/.gates/*.json`, PR links in `03-units.yaml` |
| Audit logging | `audit_log.py`, hooks | `audit.jsonl`, `verify` output, CSV export |
| Secure SDLC | Bolts with tests, license scan and SBOM from CI | `03-units.yaml`, `adlc/.state/evidence/*.json` |
| AI model governance | Approved-model list, pins per phase, ADRs for changes | `model_policy.json`, ADRs, G2 approval |
| Third-party / tool risk | MCP allow-list, dry-run write tools until release | `mcp_allowlist.json`, `policy.blocked` events |
| Data protection | Classification, pointer-only restricted data, PII scan | Policy reports per phase |
| Release and rollback | Pinned versions, staged rollout, rehearsed rollback | `05-release.md`, G5 approvals |
| Monitoring and improvement | Phase 06 against AIPRS success criteria | `06-backlog.md`, G6 approval |

These controls produce evidence that supports frameworks such as SOC 2, ISO/IEC 27001 and ISO/IEC 42001. Certification depends on the client's wider environment and an independent assessor, so present this as evidence, not as a compliance claim.

## 4. What the client's platform team provides

The package cannot supply these; plan them in the pilot:

1. **Identity.** The VS Code extension signs users in with the client's IdP and sets `ADLC_IDENTITY` and `ADLC_GROUPS` from the token. Without it, the scripts fall back to git email and static members, which is acceptable for pilots only.
2. **Model gateway.** A gateway URL for managed settings, with the client's logging and data-retention terms.
3. **CI evidence.** Jobs that run the license scan and SBOM and write the evidence files, plus a deploy job that runs `adlc_gate.py check --gate G5` and fails closed.
4. **Log shipping.** Forward `adlc/.audit/audit.jsonl` to the SIEM or WORM storage on every push.
5. **Branch protection.** Require review on the default branch and on `adlc/**`, so gate files cannot be merged without review.
6. **MDM.** Push `managed-settings.example.json` to the OS-level managed settings location.

## 5. Suggested rollout

| Stage | Scope | Exit criteria |
|---|---|---|
| Pilot (4–6 weeks) | One team, one real intent, static roles | All six gates exercised; audit chain verified; one rollback rehearsed |
| Controlled | 3–5 teams, IdP roles, CI evidence, managed settings | No `policy.blocked` false positives open > 1 week; auditors accept the evidence pack |
| General | Org-wide, reference store enabled | Platform team owns allow-lists and model policy through their normal change process |

## 6. Known limits to disclose

- Hash chaining detects tampering after the fact; it does not prevent someone with repo write access from rewriting history. Branch protection, signed commits and off-repo log shipping close that gap.
- Local policy checks are pattern-based. They reduce risk; they do not replace the client's DLP and secret-scanning tools, which should run in CI too.
- Hook and managed-settings key names should be checked against the Claude Code version the client deploys.
