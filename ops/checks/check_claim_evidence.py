import csv
from pathlib import Path
import sys


REQUIRED_COLUMNS = {
    "id",
    "type",
    "text_or_item",
    "section_or_module",
    "evidence_id",
    "source_path",
    "figure_or_table",
    "permitted_wording",
    "forbidden_wording",
    "test_id",
    "status",
    "action",
    "owner",
    "gate",
}

ALLOWED_TYPES = {
    "claim",
    "evidence",
    "figure",
    "table",
    "equation",
    "reference",
    "decision",
    "test",
}

# Canonical status vocabulary (see AGENTS.md and STED-RW_Lean.md section 13.3).
# Compared case-insensitively (pending_evidence == PENDING_EVIDENCE); the
# canonical written form is upper-case. Legacy short tokens (pending, blocked,
# verified) are intentionally no longer accepted.
ALLOWED_STATUSES = {
    "VERIFIED",
    "PARTIALLY_VERIFIED",
    "PENDING_EVIDENCE",
    "BLOCKED_BY_EVIDENCE",
    "REFERENCE_NOT_VERIFIED",
    "OBSOLETE",
    "OUT_OF_SCOPE",
}

TEMPLATE_IDS = {"TEMPLATE_CORE"}


def main() -> int:
    path = Path("ops/sted/traceability_matrix.csv")
    if not path.exists():
        print("Missing ops/sted/traceability_matrix.csv")
        return 1

    with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            print("Traceability matrix exists but does not have a header row.")
            return 1

        normalized_fieldnames = [name.strip() for name in reader.fieldnames]
        missing_columns = sorted(REQUIRED_COLUMNS.difference(normalized_fieldnames))
        if missing_columns:
            print(
                "Traceability matrix exists but is missing required columns: "
                + ", ".join(missing_columns)
            )
            return 1

        rows = list(reader)

    if not rows:
        print("Traceability matrix exists but contains no data rows.")
        return 1

    row_ids = {row.get("id", "").strip() for row in rows if row.get("id")}
    invalid_types = sorted(
        {
            row.get("type", "").strip()
            for row in rows
            if row.get("type", "").strip() and row.get("type", "").strip() not in ALLOWED_TYPES
        }
    )
    if invalid_types:
        print(
            "Traceability matrix contains unsupported type values: "
            + ", ".join(invalid_types)
        )
        return 1

    invalid_statuses = sorted(
        {
            row.get("status", "").strip()
            for row in rows
            if row.get("status", "").strip()
            and row.get("status", "").strip().upper() not in ALLOWED_STATUSES
        }
    )
    if invalid_statuses:
        print(
            "Traceability matrix contains unsupported status values: "
            + ", ".join(invalid_statuses)
        )
        return 1

    if row_ids == TEMPLATE_IDS:
        print("Lean traceability matrix scaffold exists with a recognized structure.")
        return 0

    print("Lean traceability matrix exists with a recognized structure.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
