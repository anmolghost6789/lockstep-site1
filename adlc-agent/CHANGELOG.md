# Changelog

## 1.1.0

- **Evaluation runner** (`eval_run.py`): runs a suite, reads thresholds from the approved AIPRS, writes the scorecard, compares with and without a pack.
- **Recovery** (`recover.py`): diagnoses interrupted or inconsistent runs; routes changes to the phase that owns them and voids the gates they invalidate.
- **Agent routing** (`route.py` and `config/governance/agent_catalog.json`): approved agent and model per phase or unit, with reasons; evaluators never evaluate their own work.
- **Metrics** (`metrics.py`): delivery metrics per phase, opt-in push to the registry, fixed schema that refuses content.
- **Pack manager** (`pack.py`): install, upgrade with local-edit protection, verify, roll back.
- **Pull-request gates** (`gate_github.py`, `setup_codeowners.py`) are now the default; script gates remain as local mode.
- Ported utilities, references, contracts, docs and the pilot playbook.

## 1.0.0

- Six phase skills, shared protocol, templates, contracts, policy hooks and subagents.
