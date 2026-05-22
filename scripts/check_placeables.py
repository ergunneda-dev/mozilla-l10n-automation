#!/usr/bin/env python3
"""
check_placeables.py — Find placeable mismatches between en-US and a locale.

"Placeables" are the dynamic bits embedded in a Fluent message:
    { $variable }   variable reference   (e.g., "{ $name } closed the tab")
    { -term }       term reference       (e.g., "{ -brand-short-name }")
    { message }     message reference

A translation MUST contain the same set of variable and term references as
its source, or the runtime will either crash or substitute "{ $name }"
literally into the UI. This is the single highest-signal QA check you can
run on a Fluent locale, and it's where a lot of real bugs hide.

What this script does, per matching .ftl file:
  - Parse both en-US and locale.
  - For every message present in both, extract the set of placeables in
    the value AND in each attribute.
  - Report:
      * placeables in source missing from translation
      * placeables in translation that don't exist in source (a likely typo)

Usage:
    python check_placeables.py <en-US dir> <locale dir>

Example:
    python check_placeables.py ~/firefox-l10n/en-US ~/firefox-l10n/tr
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

from fluent.syntax import parse
from fluent.syntax import ast


# ---------- file walking (same shape as audit_missing.py) ----------

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


# ---------- the actual placeable extraction ----------

def extract_placeables(node: ast.SyntaxNode) -> Set[str]:
    """
    Walk a Fluent AST subtree and return the set of placeable identifiers.

    Encoded as:
        "$name"            for VariableReference($name)
        "-term"            for TermReference(-term)
        "msg-id"           for MessageReference(msg-id)

    We use string prefixes so the three kinds can't collide.

    Selectors (the `*[other]`-style branches in `select { ... }`) contain
    multiple Pattern branches; we union all of their placeables, because
    a translator only needs to *reference* the same variables, not pick
    the same branch.
    """
    found: Set[str] = set()

    def visit(n):
        if n is None:
            return
        cls = n.__class__.__name__
        if cls == "VariableReference":
            found.add("$" + n.id.name)
        elif cls == "TermReference":
            found.add("-" + n.id.name)
        elif cls == "MessageReference":
            found.add(n.id.name)
        # Recurse into children. fluent.syntax AST nodes expose their
        # children via their attribute dict; we just iterate everything
        # that looks like an AST node or a list of them.
        for attr_name in vars(n):
            child = getattr(n, attr_name)
            if isinstance(child, ast.BaseNode):
                visit(child)
            elif isinstance(child, list):
                for item in child:
                    if isinstance(item, ast.BaseNode):
                        visit(item)

    visit(node)
    return found


def placeables_for_entry(entry: ast.Message | ast.Term) -> Dict[str, Set[str]]:
    """
    Return a dict keyed by "" (the main value) and each attribute name,
    mapping to the set of placeables in that pattern.

    Splitting by attribute matters: a missing `{ $name }` in the .tooltiptext
    is a different bug from a missing one in the main value.
    """
    result: Dict[str, Set[str]] = {}
    if entry.value is not None:
        result[""] = extract_placeables(entry.value)
    for attr in entry.attributes:
        result["." + attr.id.name] = extract_placeables(attr.value)
    return result


# ---------- diffing and reporting ----------

def diff_entry(
    en_entry: ast.Message | ast.Term,
    loc_entry: ast.Message | ast.Term,
) -> List[Tuple[str, Set[str], Set[str]]]:
    """
    Compare placeables for one message. Returns a list of (slot, missing, extra) issues:
        ('',       {'$count'}, set())    # main value lacks $count
        ('.label', set(),      {'$urll'}) # attribute has a placeable not in source
    """
    issues = []
    en_slots = placeables_for_entry(en_entry)
    loc_slots = placeables_for_entry(loc_entry)
    all_slots = set(en_slots) | set(loc_slots)
    for slot in sorted(all_slots):
        en_set = en_slots.get(slot, set())
        loc_set = loc_slots.get(slot, set())
        missing = en_set - loc_set
        extra = loc_set - en_set
        if missing or extra:
            issues.append((slot, missing, extra))
    return issues


def run(en_dir: Path, loc_dir: Path) -> int:
    en_files = set(iter_ftl_files(en_dir))
    loc_files = set(iter_ftl_files(loc_dir))
    common = sorted(en_files & loc_files)

    total_issues = 0
    for rel in common:
        try:
            en_msgs = load_messages(en_dir / rel)
            loc_msgs = load_messages(loc_dir / rel)
        except Exception as e:
            print(f"[{rel}] PARSE ERROR: {e}")
            continue

        file_issues: List[str] = []
        for mid, en_entry in en_msgs.items():
            if mid not in loc_msgs:
                continue  # missing messages are audit_missing.py's job
            for slot, missing, extra in diff_entry(en_entry, loc_msgs[mid]):
                slot_label = f"{mid}{slot}" if slot else mid
                if missing:
                    file_issues.append(f"  missing in translation: {slot_label}  →  {sorted(missing)}")
                if extra:
                    file_issues.append(f"  extra in translation:   {slot_label}  →  {sorted(extra)}")

        if file_issues:
            print(f"\n[{rel}]")
            for line in file_issues:
                print(line)
            total_issues += len(file_issues)

    print(f"\n## Summary: {total_issues} placeable issue(s)")
    return 1 if total_issues else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("en_dir", type=Path)
    parser.add_argument("locale_dir", type=Path)
    args = parser.parse_args()

    for label, path in [("en_dir", args.en_dir), ("locale_dir", args.locale_dir)]:
        if not path.is_dir():
            print(f"error: {label} {path} is not a directory", file=sys.stderr)
            return 2

    return run(args.en_dir, args.locale_dir)


if __name__ == "__main__":
    sys.exit(main())
# Edited to test PR audit workflow.
