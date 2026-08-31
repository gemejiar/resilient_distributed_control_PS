from pathlib import Path
import sys

# Canonical manuscript bibliography. Keep in sync with:
#   ops/checks/check_latex_structure.py  (--bib-file default)
#   AI_TOOLS/hooks/post_edit_check.py    (GOVERNED_PREFIXES)
CANONICAL_BIB = Path("Paper_manuscript/references.bib")


def main() -> int:
    if not CANONICAL_BIB.exists():
        print(f"Missing canonical bibliography file: {CANONICAL_BIB.as_posix()}")
        return 1
    if not CANONICAL_BIB.read_text(encoding="utf-8", errors="ignore").strip():
        print(f"Canonical bibliography file is empty: {CANONICAL_BIB.as_posix()}")
        return 1
    print(f"Canonical bibliography file exists: {CANONICAL_BIB.as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
