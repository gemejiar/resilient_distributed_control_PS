from argparse import ArgumentParser, Namespace
from pathlib import Path
import re
import sys

PATTERNS = [
    r"state[- ]of[- ]the[- ]art",
    r"best model overall",
    r"deep learning outperforms all baselines",
    r"generalize[s]? to all power systems",
]

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
    "all",
)

CORE_SCAN_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "plan_maestro.md",
    "ops/sted/traceability_matrix.csv",
    "ops/sted/final_quality_report.md",
]

PROJECT_TYPE_DIRS = {
    "paper": ["paper"],
    "review": ["paper"],
    "chapter": ["paper"],
    "thesis": ["paper"],
    "proposal": ["paper", "src/docs"],
    "book": ["book"],
    "software": ["src/docs"],
    "pipeline": ["src/docs"],
    "course": ["src/docs"],
    "all": ["paper", "book", "src/docs"],
}

TEXT_SUFFIXES = {
    ".bib",
    ".csv",
    ".json",
    ".md",
    ".rst",
    ".tex",
    ".txt",
    ".tsv",
    ".yaml",
    ".yml",
}


def parse_args() -> Namespace:
    parser = ArgumentParser(
        description=(
            "Scan Lean core artifacts and project deliverable text files for "
            "forbidden overclaim patterns."
        )
    )
    parser.add_argument(
        "--project-type",
        choices=PROJECT_TYPES,
        default="auto",
        help="Active STED-RW project type. Defaults to auto-detection from existing deliverable directories.",
    )
    return parser.parse_args()


def iter_project_dirs(root: Path, project_type: str) -> list[Path]:
    if project_type == "auto":
        candidates = ["paper", "book", "src/docs"]
    else:
        candidates = PROJECT_TYPE_DIRS.get(project_type, [])
    return [root / rel for rel in candidates if (root / rel).exists()]


def iter_scan_files(root: Path, project_type: str) -> list[Path]:
    seen: set[Path] = set()
    files: list[Path] = []

    for rel in CORE_SCAN_FILES:
        path = root / rel
        if path.exists() and path not in seen:
            seen.add(path)
            files.append(path)

    for directory in iter_project_dirs(root, project_type):
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if path not in seen:
                seen.add(path)
                files.append(path)

    return files


def main() -> int:
    args = parse_args()
    root = Path.cwd()
    findings = []
    scan_files = iter_scan_files(root, args.project_type)
    for path in scan_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                findings.append((path.relative_to(root).as_posix(), pattern))
    if findings:
        print("FORBIDDEN CLAIM PATTERNS FOUND:")
        for rel, pattern in findings:
            print(f"{rel}: {pattern}")
        return 1
    print(f"No forbidden claim patterns found in {len(scan_files)} scanned files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
