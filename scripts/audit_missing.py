#!/usr/bin/env python3
"""
audit_missing.py — Compare a locale tree to en-US and report missing/empty messages.

Walks every .ftl file in EN_DIR, finds the matching file in LOCALE_DIR, and prints:
  - messages present in en-US but absent in the locale (missing)
  - messages present in both but with an empty value (empty)
  - .ftl files that exist in en-US but not in the locale (missing file)
  - .ftl files that exist in the locale but not in en-US (obsolete file)

Why this matters:
  This is the "how complete is locale X?" question, the most common
  starting point for any l10n automation. Real production code should
  use `compare-locales`; this script exists to make the underlying
  pattern (parse → walk → diff) explicit.

Usage:
    python audit_missing.py <en-US dir> <locale dir>

Example:
    python audit_missing.py ~/firefox-l10n/en-US ~/firefox-l10n/tr
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, Tuple

from fluent.syntax import parse
from fluent.syntax import ast


def iter_ftl_files(root: Path) -> Iterable[Path]:
    """Yield every .ftl file under `root`, as paths relative to `root`."""
    for p in root.rglob("*.ftl"):
        yield p.relative_to(root)


def load_messages(path: Path) -> Dict[str, ast.Message | ast.Term]:
    """
    Parse a Fluent file and return {id: entry} for every Message and Term.

    Terms (ids starting with `-`) are included because translators sometimes
    leave them empty too, and they're real entries in the AST.
    """
    text = path.read_text(encoding="utf-8")
    resource = parse(text)
    out: Dict[str, ast.Message | ast.Term] = {}
    for entry in resource.body:
        if isinstance(entry, ast.Message):
            out[entry.id.name] = entry
        elif isinstance(entry, ast.Term):
            out["-" + entry.id.name] = entry
    return out


def is_empty(entry: ast.Message | ast.Term) -> bool:
    """
    A message is "empty" if it has no value AND no attributes.

    Note: a message with only attributes (no main value) is valid Fluent
    — the .label/.tooltiptext patterns rely on it — so we don't flag those.
    """
    has_value = entry.value is not None
    has_attrs = bool(entry.attributes)
    return not (has_value or has_attrs)


def audit(en_dir: Path, loc_dir: Path) -> Tuple[int, int, int, int]:
    """Run the audit and print findings. Returns (missing, empty, missing_files, obsolete_files)."""
    en_files = set(iter_ftl_files(en_dir))
    loc_files = set(iter_ftl_files(loc_dir))

    missing_files = en_files - loc_files
    obsolete_files = loc_files - en_files

    if missing_files:
        print(f"\n## Missing files ({len(missing_files)})")
        for rel in sorted(missing_files):
            print(f"  - {rel}")

    if obsolete_files:
        print(f"\n## Obsolete files in locale ({len(obsolete_files)})")
        for rel in sorted(obsolete_files):
            print(f"  - {rel}")

    total_missing = 0
    total_empty = 0

    print(f"\n## Per-file findings")
    for rel in sorted(en_files & loc_files):
        try:
            en_msgs = load_messages(en_dir / rel)
            loc_msgs = load_messages(loc_dir / rel)
        except Exception as e:
            print(f"\n[{rel}] PARSE ERROR: {e}")
            continue

        missing = [mid for mid in en_msgs if mid not in loc_msgs]
        # "Empty" means: present in locale, but the locale entry has no value/attrs.
        empty = [mid for mid in en_msgs if mid in loc_msgs and is_empty(loc_msgs[mid])]

        if missing or empty:
            print(f"\n[{rel}]")
            for mid in missing:
                print(f"  missing: {mid}")
            for mid in empty:
                print(f"  empty:   {mid}")
            total_missing += len(missing)
            total_empty += len(empty)

    print(f"\n## Summary")
    print(f"  Missing messages:  {total_missing}")
    print(f"  Empty messages:    {total_empty}")
    print(f"  Missing files:     {len(missing_files)}")
    print(f"  Obsolete files:    {len(obsolete_files)}")

    return total_missing, total_empty, len(missing_files), len(obsolete_files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("en_dir", type=Path, help="Path to the en-US locale tree")
    parser.add_argument("locale_dir", type=Path, help="Path to the target locale tree")
    args = parser.parse_args()

    for label, path in [("en_dir", args.en_dir), ("locale_dir", args.locale_dir)]:
        if not path.is_dir():
            print(f"error: {label} {path} is not a directory", file=sys.stderr)
            return 2

    missing, empty, _, _ = audit(args.en_dir, args.locale_dir)
    # Non-zero exit when there's work to do — useful in CI.
    return 1 if (missing or empty) else 0


if __name__ == "__main__":
    sys.exit(main())
