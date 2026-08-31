# Validation Rules

- Run `python ops/checks/check_required_files.py` before claiming the Lean template `required_core` is structurally ready.
- Use only validations that correspond to the active project type; avoid paper-only checks for non-paper projects.
- Do not treat missing tool adapters or prompt packs as Lean-core failures unless the active workflow explicitly depends on them.
- Use `python ops/checks/check_required_files.py --strict` only when you need adapter-complete or instantiated-project readiness.
- Record structural exceptions or deferred validations in `ops/sted/decision_log.md`.
