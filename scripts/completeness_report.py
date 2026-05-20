#!/usr/bin/env python3
"""
completeness_report.py — Per-locale completion percentages as a CSV.

Crawls a multi-locale repo, computes for each locale:
    en_messages       total messages+terms in en-US
    translated        messages present and non-empty in the locale
    missing           in en-US but absent
    empty             present but value-less and attribute-less
    parse_errors      .ftl files that failed to parse
    percent_complete  100 * translated / en_messages

Writes the result as a CSV that's easy to drop into a spreadsheet or
weekly status post.

Usage:
    python completeness_report.py <repo root> [--out report.csv] [--en-locale en-US]

Example:
    python completeness_report.py ~/firefox-l10n --out /tmp/l10n_report.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, Iterable, Tuple

from fluent.syntax import parse
from fluent.syntax import ast


def iter_ftl_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.ftl"):
        yield p.relative_to(root)


def load_messages(path: Path) -> Dict[str, ast.Message | ast.Term]:
    resource = parse(path.read_text(encoding="utf-8"))
    out: Dict[str, ast.Message | ast.Term] = {}
    for entry in resource.body:
        if isinstance(entry, ast.Message):
            out[entry.id.name] = entry
        elif isinstance(entry, ast.Term):
            out["-" + entry.id.name] = entry
    return out


def is_empty(entry: ast.Message | ast.Term) -> bool:
    return entry.value is None and not entry.attributes


def count_en_messages(en_dir: Path) -> Dict[Path, Dict[str, ast.Message | ast.Term]]:
    """Cache the en-US message dictionary per file — every locale compares against it."""
    out: Dict[Path, Dict[str, ast.Message | ast.Term]] = {}
    for rel in iter_ftl_files(en_dir):
        try:
            out[rel] = load_messages(en_dir / rel)
        except Exception as e:
            print(f"warning: en-US parse error in {rel}: {e}", file=sys.stderr)
            out[rel] = {}
    return out


def stats_for_locale(en_msgs_by_file: Dict[Path, Dict[str, ast.Message | ast.Term]],
                     loc_dir: Path) -> Tuple[int, int, int, int, int]:
    """Return (en_total, translated, missing, empty, parse_errors) for one locale dir."""
    en_total = sum(len(m) for m in en_msgs_by_file.values())
    translated = 0
    missing = 0
    empty = 0
    parse_errors = 0

    for rel, en_msgs in en_msgs_by_file.items():
        loc_path = loc_dir / rel
        if not loc_path.exists():
            # The whole file is missing → every en-US message in it is missing.
            missing += len(en_msgs)
            continue
        try:
            loc_msgs = load_messages(loc_path)
        except Exception:
            parse_errors += 1
            # Treat unparseable file as fully missing rather than fully translated.
            missing += len(en_msgs)
            continue
        for mid in en_msgs:
            if mid not in loc_msgs:
                missing += 1
            elif is_empty(loc_msgs[mid]):
                empty += 1
            else:
                translated += 1

    return en_total, translated, missing, empty, parse_errors


def discover_locale_dirs(repo_root: Path, en_locale: str) -> Iterable[Path]:
    for child in sorted(repo_root.iterdir()):
        if not child.is_dir() or child.name.startswith(".") or child.name == en_locale:
            continue
        try:
            next(child.rglob("*.ftl"))
        except StopIteration:
            continue
        yield child


def run(repo_root: Path, out_path: Path | None, en_locale: str) -> int:
    en_dir = repo_root / en_locale
    if not en_dir.is_dir():
        print(f"error: en locale dir {en_dir} not found", file=sys.stderr)
        return 2

    print(f"loading en-US ({en_locale})...", file=sys.stderr)
    en_msgs = count_en_messages(en_dir)
    en_total = sum(len(m) for m in en_msgs.values())
    print(f"  {en_total} messages across {len(en_msgs)} files", file=sys.stderr)

    rows = []
    for loc_dir in discover_locale_dirs(repo_root, en_locale):
        print(f"scanning {loc_dir.name}...", file=sys.stderr)
        total, translated, missing, empty, errors = stats_for_locale(en_msgs, loc_dir)
        pct = (100.0 * translated / total) if total else 0.0
        rows.append({
            "locale": loc_dir.name,
            "en_messages": total,
            "translated": translated,
            "missing": missing,
            "empty": empty,
            "parse_errors": errors,
            "percent_complete": f"{pct:.2f}",
        })

    rows.sort(key=lambda r: float(r["percent_complete"]), reverse=True)

    fieldnames = ["locale", "en_messages", "translated", "missing",
                  "empty", "parse_errors", "percent_complete"]

    if out_path:
        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nwrote {out_path}", file=sys.stderr)
    else:
        # Pretty-print to stdout if no --out given.
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repo_root", type=Path, help="Root of the locale repo")
    parser.add_argument("--out", type=Path, default=None, help="CSV output path (default: stdout)")
    parser.add_argument("--en-locale", default="en-US", help="Reference locale directory name (default: en-US)")
    args = parser.parse_args()

    if not args.repo_root.is_dir():
        print(f"error: {args.repo_root} is not a directory", file=sys.stderr)
        return 2

    return run(args.repo_root, args.out, args.en_locale)


if __name__ == "__main__":
    sys.exit(main())
