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

REQUIRED_SECTIONS = [
    r"\section{Introduction}",
    r"\section{Related Work}",
    r"\section{Methodology}",
    r"\section{Experimental Setup}",
    r"\section{Results}",
    r"\section{Discussion}",
    r"\section{Limitations}",
    r"\section{Conclusion}",
]


def parse_args() -> Namespace:
    parser = ArgumentParser(
        description=(
            "Validate the canonical LaTeX paper structure only when the active "
            "project context corresponds to a LaTeX paper deliverable."
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
        default="paper/main.tex",
        help="Main LaTeX manuscript file to validate.",
    )
    parser.add_argument(
        "--bib-file",
        default="paper/bibliography/references.bib",
        help="BibTeX file required by the canonical paper layout.",
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

    required = [main_path, bib_path]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print("MISSING LATEX STRUCTURE FILES:")
        for path in missing:
            print(path)
        return 1

    main_text = main_path.read_text(encoding="utf-8", errors="ignore")
    if r"\input{" in main_text or r"\include{" in main_text:
        print(f"{main_path.as_posix()} must not use \\input{{}} or \\include{{}} for manuscript sections.")
        return 1

    cursor = 0
    for section in REQUIRED_SECTIONS:
        idx = main_text.find(section, cursor)
        if idx == -1:
            print(f"Missing or out-of-order section: {section}")
            return 1
        cursor = idx + len(section)
    print("Canonical LaTeX structure is present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
