from argparse import ArgumentParser, Namespace
from pathlib import Path
import sys


REQUIRED_CORE = [
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "STED-RW_Lean.md",
    "prompt_maestro_STED_RW.md",
    "ops/README.md",
    "ops/sted/traceability_matrix.csv",
    "ops/sted/test_plan.md",
    "ops/sted/decision_log.md",
    "ops/sted/final_quality_report.md",
    "ops/sted/agents_catalog.md",
    ".claude/agents/sted_integrator.md",
]

OPTIONAL_ADAPTERS = [
    ".agents/orchestrator.md",
    ".agents/skills/sted-rw/SKILL.md",
    ".codex/instructions.md",
    ".codex/project_context.md",
    ".codex/methodology_rules.md",
    ".codex/research_rules.md",
    ".codex/latex_rules.md",
    ".codex/validation_rules.md",
    ".codex/prompts/sted-execute.md",
    ".codex/prompts/sted-verify.md",
]

MODE_REQUIREMENTS = {
    "template": [],
    "paper": [
        "plan_maestro.md",
        "paper/main.tex",
    ],
    "book": [
        "plan_maestro.md",
        "book/main.tex",
    ],
    "software": [
        "plan_maestro.md",
        "software/README.md",
    ],
    "pipeline": [
        "plan_maestro.md",
        "pipeline/README.md",
    ],
}


def parse_args() -> Namespace:
    parser = ArgumentParser(
        description=(
            "Validate the STED-RW Lean repository structure. "
            "Template mode checks only the Lean core; project modes add "
            "deliverable-specific requirements."
        )
    )
    parser.add_argument(
        "--mode",
        choices=sorted(MODE_REQUIREMENTS),
        default="template",
        help=(
            "Validation mode. Use 'template' for the base scaffold, or a "
            "project mode such as 'paper' to require project deliverables."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Fail if optional_adapters are missing in addition to the selected "
            "mode requirements."
        ),
    )
    return parser.parse_args()


def find_missing(root: Path, paths: list[str]) -> list[str]:
    return [path for path in paths if not (root / path).exists()]


def print_group(title: str, paths: list[str], note: str | None = None) -> None:
    print(title)
    if note:
        print(note)
    for path in paths:
        print(path)


def main() -> int:
    args = parse_args()
    root = Path.cwd()

    exit_code = 0

    missing_core = find_missing(root, REQUIRED_CORE)
    if missing_core:
        print_group("MISSING REQUIRED_CORE FILES:", missing_core)
        exit_code = 1
    else:
        print("STED-RW Lean required_core is present.")

    missing_optional = find_missing(root, OPTIONAL_ADAPTERS)
    if missing_optional:
        print()
        print_group(
            "MISSING OPTIONAL_ADAPTERS FILES:",
            missing_optional,
            note="Non-blocking for Lean core; install only when the workflow depends on them.",
        )
        if args.strict:
            exit_code = 1

    mode_requirements = MODE_REQUIREMENTS[args.mode]
    if args.mode == "template":
        print()
        print("Template mode selected: skipping project deliverable checks.")
    else:
        missing_mode = find_missing(root, mode_requirements)
        if missing_mode:
            print()
            print_group(
                f"MISSING {args.mode.upper()} MODE FILES:",
                missing_mode,
                note=(
                    "Blocking for the selected project mode; instantiate the "
                    "project scaffold before claiming this mode is ready."
                ),
            )
            exit_code = 1
        else:
            print()
            print(f"{args.mode.capitalize()} mode requirements are present.")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
