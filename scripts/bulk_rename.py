#!/usr/bin/env python3
"""
bulk_rename.py — Safe find-and-replace across every locale .ftl file.

Use case: marketing/legal renames a brand term ("Firefox Account" →
"Mozilla account") and you need to propagate it across every locale,
without breaking selectors, attributes, or comments.

Why this exists instead of `sed -i`:
  - sed will happily corrupt multiline messages, selectors, and the
    inside of `{ $variable }` blocks. With Fluent you MUST parse, modify
    the text patterns only, and serialize back.
  - We touch only Pattern.TextElement nodes — never identifiers, never
    placeables, never comments-that-are-actually-license-headers.

Safety model:
  - Default mode is dry-run: prints every change it would make, writes nothing.
  - `--apply` is the explicit opt-in to write files.
  - `--locales tr,de,fr` to limit blast radius during testing.
  - Source-of-truth en-US is skipped unless `--include-en-us` is passed
    (you almost never want to do that).

Usage:
    python bulk_rename.py <repo root> "<old text>" "<new text>" [--apply] [--locales tr,de]

Example:
    # Preview only:
    python bulk_rename.py ~/firefox-l10n "Firefox Account" "Mozilla account"

    # Actually write changes for just the Turkish locale:
    python bulk_rename.py ~/firefox-l10n "Firefox Account" "Mozilla account" --locales tr --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

from fluent.syntax import parse, serialize
from fluent.syntax import ast


def iter_locale_dirs(repo_root: Path, include_en_us: bool) -> Iterable[Path]:
    """
    A 'locale dir' is any immediate subdirectory of repo_root that contains
    at least one .ftl file. This catches firefox-l10n's layout without
    requiring a hardcoded list of locale codes.
    """
    for child in sorted(repo_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name == "en-US" and not include_en_us:
            continue
        if child.name.startswith("."):
            continue
        # Quick existence check: does this dir hold .ftl files anywhere?
        try:
            next(child.rglob("*.ftl"))
        except StopIteration:
            continue
        yield child


def rewrite_text_in_pattern(pattern: ast.Pattern, old: str, new: str) -> int:
    """
    Replace `old` with `new` inside every TextElement of a Pattern.

    Returns the number of substitutions made.

    KEY POINT: Pattern.elements is a list of either TextElement (literal
    text in the message) or Placeable (the `{ ... }` blocks). We only ever
    touch TextElement.value, which is just a Python string. This is the
    surgical-edit guarantee — placeables are left alone.
    """
    count = 0
    for el in pattern.elements:
        if isinstance(el, ast.TextElement):
            if old in el.value:
                count += el.value.count(old)
                el.value = el.value.replace(old, new)
        elif isinstance(el, ast.Placeable):
            # Placeables can contain SelectExpressions whose variants
            # are themselves Patterns. Recurse into them.
            expr = el.expression
            if isinstance(expr, ast.SelectExpression):
                for variant in expr.variants:
                    count += rewrite_text_in_pattern(variant.value, old, new)
    return count


def rewrite_file(path: Path, old: str, new: str) -> Tuple[int, str]:
    """
    Parse `path`, perform replacements, and return (substitution_count, new_text).
    Does NOT write to disk — caller decides.
    """
    src = path.read_text(encoding="utf-8")
    resource = parse(src)
    total = 0

    for entry in resource.body:
        if isinstance(entry, (ast.Message, ast.Term)):
            if entry.value is not None:
                total += rewrite_text_in_pattern(entry.value, old, new)
            for attr in entry.attributes:
                total += rewrite_text_in_pattern(attr.value, old, new)

    return total, serialize(resource)


def run(repo_root: Path, old: str, new: str, apply: bool,
        locales_filter: List[str], include_en_us: bool) -> int:
    if old == new:
        print("error: old and new strings are identical", file=sys.stderr)
        return 2
    if not old:
        print("error: old string must be non-empty", file=sys.stderr)
        return 2

    locale_dirs = list(iter_locale_dirs(repo_root, include_en_us=include_en_us))
    if locales_filter:
        wanted = set(locales_filter)
        locale_dirs = [d for d in locale_dirs if d.name in wanted]
        missing = wanted - {d.name for d in locale_dirs}
        if missing:
            print(f"warning: locales not found: {sorted(missing)}", file=sys.stderr)

    if not locale_dirs:
        print("error: no locale directories matched", file=sys.stderr)
        return 2

    grand_total = 0
    files_touched = 0

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[{mode}] '{old}' → '{new}' across {len(locale_dirs)} locale(s)")

    for loc_dir in locale_dirs:
        loc_count = 0
        for ftl in sorted(loc_dir.rglob("*.ftl")):
            try:
                n, new_text = rewrite_file(ftl, old, new)
            except Exception as e:
                print(f"  [{ftl.relative_to(repo_root)}] PARSE ERROR: {e}")
                continue
            if n == 0:
                continue
            files_touched += 1
            loc_count += n
            rel = ftl.relative_to(repo_root)
            print(f"  {rel}: {n} replacement(s)")
            if apply:
                ftl.write_text(new_text, encoding="utf-8")
        if loc_count:
            print(f"  → {loc_dir.name}: {loc_count} replacement(s)")
        grand_total += loc_count

    print(f"\n## Summary")
    print(f"  Files affected:      {files_touched}")
    print(f"  Total replacements:  {grand_total}")
    if not apply:
        print(f"  (dry-run — re-run with --apply to write changes)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repo_root", type=Path, help="Root of the locale repo (firefox-l10n etc.)")
    parser.add_argument("old", help="Text to find (literal, case-sensitive)")
    parser.add_argument("new", help="Text to replace with")
    parser.add_argument("--apply", action="store_true", help="Actually write changes (default: dry-run)")
    parser.add_argument("--locales", default="", help="Comma-separated locale codes to limit to")
    parser.add_argument("--include-en-us", action="store_true",
                        help="Also rewrite en-US (you almost never want this)")
    args = parser.parse_args()

    if not args.repo_root.is_dir():
        print(f"error: {args.repo_root} is not a directory", file=sys.stderr)
        return 2

    locales = [s.strip() for s in args.locales.split(",") if s.strip()]
    return run(args.repo_root, args.old, args.new, args.apply, locales, args.include_en_us)


if __name__ == "__main__":
    sys.exit(main())
