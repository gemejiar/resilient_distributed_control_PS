from pathlib import Path
import sys


def main() -> int:
    path = Path("paper/biblio_paper.bib")
    if not path.exists():
        print("Missing canonical bibliography file.")
        return 1
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        print("Canonical bibliography file is empty.")
        return 1
    print("Canonical bibliography file exists.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
