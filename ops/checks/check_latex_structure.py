from argparse import ArgumentParser, Namespace
from pathlib import Path
import sys

PROJECT_TYPES = (
    "auto",
    "paper",
    "book",
    "software",
    "pipeline",
    "review",
    "chapter",
    "thesis",
    "proposal",
    "course",
)

PAPER_FORMATS = ("auto", "latex", "markdown", "docx", "none")


def parse_args() -> Namespace:
    parser = ArgumentParser(
        description=(
            "Presence check for the canonical LaTeX manuscript files. This is "
            "NOT an editorial gate: section names, ordering, and whether the "
            r"manuscript uses \input{}/\include{} are governed by the target "
            "venue and plan_maestro.md, not by this script."
        )
    )
    parser.add_argument(
        "--project-type",
        choices=PROJECT_TYPES,
        default="auto",
        help="Active STED-RW project type. Defaults to auto-detection.",
    )
    parser.add_argument(
        "--paper-format",
        choices=PAPER_FORMATS,
        default="auto",
        help="Deliverable format for paper-like projects. Defaults to auto-detection.",
    )
    parser.add_argument(
        "--main-file",
        default="Paper_manuscript/main.tex",
        help="Main LaTeX manuscript file.",
    )
    parser.add_argument(
        "--bib-file",
        default="Paper_manuscript/references.bib",
        help="BibTeX file for the canonical manuscript layout.",
    )
    return parser.parse_args()


def should_run(args: Namespace, main_path: Path, bib_path: Path) -> bool:
    if args.project_type != "auto" and args.project_type != "paper":
        print(
            "Skipping LaTeX structure check because "
            f"project_type={args.project_type} is not paper."
        )
        return False

    if args.paper_format != "auto" and args.paper_format != "latex":
        print(
            "Skipping LaTeX structure check because "
            f"paper_format={args.paper_format} is not latex."
        )
        return False

    if args.project_type == "paper" or args.paper_format == "latex":
        return True

    if main_path.exists() or bib_path.exists():
        return True

    print("Skipping LaTeX structure check because no active LaTeX paper target was detected.")
    return False


def main() -> int:
    args = parse_args()
    main_path = Path(args.main_file)
    bib_path = Path(args.bib_file)

    if not should_run(args, main_path, bib_path):
        return 0

    problems = []
    for path in (main_path, bib_path):
        if not path.exists():
            problems.append(f"missing: {path.as_posix()}")
        elif not path.read_text(encoding="utf-8", errors="ignore").strip():
            problems.append(f"empty: {path.as_posix()}")

    if problems:
        print("CANONICAL MANUSCRIPT FILES NOT READY:")
        for item in problems:
            print(item)
        return 1

    print(
        "Canonical manuscript files present: "
        f"{main_path.as_posix()}, {bib_path.as_posix()}. "
        "Section structure is deferred to the target venue and plan_maestro.md."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
