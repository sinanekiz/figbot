# FIGBOT repository rules

<!-- codebase-memory-mcp:start -->
For structural codebase exploration, use the installed `codebase-memory` skill.
<!-- codebase-memory-mcp:end -->

## FIGBOT code lookup

- Use the `figbot` graph project; verify its root matches this checkout with `index_status` before structural exploration. If absent, index this repository in `fast` mode first. Do not report a failed index as ready.
- Prefer bounded symbol queries, call traces and source snippets over repeated whole-repository scans. Check coverage for every relied-on file; read missing or stale ranges directly. Use text search for literals, configuration and documentation.
- For implementation questions, start in `software/`, `scripts/`, `tests/`, `cad/` or `viewer/` as appropriate. `GUNCEL/` contains published artifacts and may duplicate implementation sources; inspect it when validating delivery or physical run evidence. Historical CAD source dependencies remain valid when referenced by current code.
- Read `MASTER_SPEC.md`, `DECISIONS.md` and `ASSUMPTIONS.md` directly for project decisions and physical validation. A graph result is not evidence that robot movement or calibration is physically verified.
- Reuse a current index; do not rebuild it or launch extra agents for each question. Keep graph results limited to the task. Use deeper analysis only when the requested work needs it.
- Prefer `search_graph` for symbols, `get_architecture` for architecture, `get_file_outline` for file declarations, `trace_path` for calls/dependencies, and `get_code_snippet` for code. If graph coverage is sufficient, avoid whole-repository scans and loading many source files. Fall back to exact source only for coverage gaps or required verification.
- If the current MCP transport is stale after a daemon restart, use the same tools through `codebase-memory-mcp cli` until Codex reconnects. The installed binary is `C:/Users/Sinan/AppData/Local/Programs/codebase-memory-mcp/codebase-memory-mcp.exe` (`0.11.0-daclfix4`), with `CBM_CACHE_DIR=C:/cbm-cache-patched` and `CBM_SKIP_DACL_HARDENING=1`. The cache requires inherited full control for the current user and Windows SYSTEM; missing SYSTEM access caused atomic replacement to fail with Windows error 5. Verify these settings before retrying `persist_failed`.

## Engineering and delivery rules

- `MASTER_SPEC.md` is the technical source of truth.
- Do not change critical dimensions without recording a decision in `DECISIONS.md`.
- Record assumptions in `ASSUMPTIONS.md`; never invent unknown values. Use `TBD`, `UNVERIFIED`, or `PHYSICAL VALIDATION REQUIRED`.
- After CAD changes, rebuild assemblies, exports, renders, URDF, and affected tests.
- After BOM changes, rebuild the cost estimate and run validation.
- Run tests for every changed module.
- Never purchase anything unless the user explicitly asks.
- Never describe unverified physical safety or strength as production-ready.
- Prefer low cost, simplicity, standard parts, repairability, and low moving mass.
- User-facing current artifacts always live in `GUNCEL/`: `BASKI`, `CAD`, `ALISVERIS`, `YAZILIM`. Use `scripts/project_paths.py`; never create version-named delivery folders again. Keep revision IDs in metadata. Previous artifacts belong in `ARSIV/ESKI_SURUMLER.zip`, with SHA256 verification before removing loose originals. Historical source modules used by current CAD remain developer dependencies, not alternative print packages. Publish through `scripts/publish_current.py`.
