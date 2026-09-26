# `outputs/`

This folder is canonical and intentionally near-empty. **Real run outputs live under `runs/run_<TS>/outputs/`** — that's the workspace the Build Agent writes into.

Some integrations may stage final, promoted deliverables here after a run is reviewed (e.g., a curator copies the approved DDL pack out of a run dir). Everything in `outputs/run_id_*/` is gitignored.
