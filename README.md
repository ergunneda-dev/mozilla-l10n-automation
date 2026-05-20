# Mozilla l10n Automation

> Tools and analyses for Mozilla's localization repositories. Four Python scripts, two GitHub Actions, two real-data reports — a portfolio project exploring localization engineering at scale.

May 2026 · [scripts](./scripts) · [contributor tutorial](./GITHUB_TUTORIAL.md) · [analyses](#highlights-from-the-real-data-runs)

---

## AI assistance disclosure

This project was built collaboratively with **Claude (Anthropic)**. Roles were roughly:

- **Me** (the human): project direction, ran the scripts against the real `firefox-l10n` repo, interpreted findings, made the judgment calls about which placeable divergences were bugs vs. intentional, identified the cross-locale patterns, framed the strategic categorizations.
- **Claude**: drafted the Python code, scaffolded the contributor tutorial, structured the GitHub Actions YAML, helped shape the analysis documents.

I've reviewed everything published here, can answer questions about how it works, and won't represent it as solo engineering work. The interesting parts are the *judgment* and the *patterns*, not the code volume — and those are mine.

## Why this exists

Mozilla maintains Firefox translations across 200+ locales via a unified GitHub repo, [`mozilla-l10n/firefox-l10n`](https://github.com/mozilla-l10n/firefox-l10n). Production tooling exists (`compare-locales`, Pontoon), but day-to-day localization-program work involves repetitive audits: completeness checks, QA scans for missing placeables, bulk term renames across locales. This project automates the most common audits with three discipline principles:

1. **Parse, don't regex.** Fluent files have selectors, attributes, and nested patterns that regex-based tools mangle. Every script here uses `fluent.syntax` AST parsing.
2. **Dry-run first.** Any mutation is preview-then-apply, never silent. Translators' work doesn't get blown away by a hasty script.
3. **Distinguish findings.** Not every "divergence" between source and translation is a bug. The analysis docs work through a three-category framework for triage.

## What's in here

| Path | Purpose |
|---|---|
| [`scripts/audit_missing.py`](./scripts/audit_missing.py) | Per-locale: missing files, missing messages, empty messages |
| [`scripts/check_placeables.py`](./scripts/check_placeables.py) | Per-locale: variables/terms present in source but missing in translation |
| [`scripts/bulk_rename.py`](./scripts/bulk_rename.py) | Safe brand-term find/replace across all locales (dry-run + `--apply`) |
| [`scripts/completeness_report.py`](./scripts/completeness_report.py) | CSV of per-locale completion percentages across the whole repo |
| [`github-actions-examples/`](./github-actions-examples) | Production-shape workflows: weekly report + per-PR placeable check |
| [`GITHUB_TUTORIAL.md`](./GITHUB_TUTORIAL.md) | Step-by-step contributor flow: fork → branch → PR → Actions |
| [`placeable-audit-2026-05-20.md`](./placeable-audit-2026-05-20.md) | Real-data analysis across 6 locales: three-category finding framework |
| [`completeness-analysis-2026-05-20.md`](./completeness-analysis-2026-05-20.md) | Real-data analysis across all 157 locales: completion distribution |
| [`UPSTREAM_PR_PLAN.md`](./UPSTREAM_PR_PLAN.md) | Plan and candidates for a real upstream PR to mozilla-l10n |
| [`l10n-completeness-2026-05-20.csv`](./l10n-completeness-2026-05-20.csv) | Raw CSV output that the completeness analysis was built from |

## Highlights from the real-data runs

**The three categories every placeable finding falls into.** Distinguishing them is the actual skill — running the script is the easy part.

1. **Deliberate simplifications.** Example: `-fxaccount-brand-name` has a `$capitalization` selector in en-US (`[sentence]` / `[title]`). Five+ locales (tr, de, es-ES, ja, zh-CN) dropped it because their languages don't need the English-style capitalization distinction. *Not bugs.*
2. **Latent runtime UI bugs.** Example: Japanese password-manager messages missing `$count` placeables. At runtime, Firefox passes a number expecting substitution; the translation has no slot for it; users see a sentence with no number. *File as bugs.*
3. **Stale references.** Example: pt-BR's `unifiedExtensions.ftl` references `$extensionsCount` — a variable no longer in the source. Doesn't crash (Fluent handles unknown refs gracefully) but should be cleaned up. *Tidy on next sync.*

**Nineteen locales at 100% completeness.** Including surprising entries: Lower Sorbian (`dsb`, ~7,000 speakers worldwide), Upper Sorbian (`hsb`), and Interlingua (`ia`, a constructed auxiliary language). Reveals tiny but extraordinarily dedicated translator communities — a fact you only see when you actually count. (en-GB is also in the 100% set; it's structurally identical to en-US, so the metric trivially passes.)

**Japanese is the outlier — 146 missing strings, 32 placeable issues.** Both concentrated in recently-landed features: GenAI chatbot, contextual password manager, PDF.js editor comments. The placeable check is therefore acting as a **leading indicator of translation freshness**, not just a static QA tool. A locale's issue count spiking up correlates with a release cycle's new strings landing.

**Catalan at 78.93%.** Anomalous given other Romance locales sit at 99–100%. The kind of finding a program manager surfaces, prioritizes, and either fixes or escalates.

[Full placeable analysis →](./placeable-audit-2026-05-20.md) · [Full completeness analysis →](./completeness-analysis-2026-05-20.md)

## Run it yourself

```bash
pip install fluent.syntax
git clone --depth=1 https://github.com/mozilla-l10n/firefox-l10n.git
git clone --depth=1 https://github.com/mozilla-l10n/firefox-l10n-source.git
cd firefox-l10n
python3 /path/to/scripts/check_placeables.py ../firefox-l10n-source tr
```

`firefox-l10n` holds only translations; the canonical en-US source lives in [`mozilla-l10n/firefox-l10n-source`](https://github.com/mozilla-l10n/firefox-l10n-source), auto-synced from `mozilla-central` by Mozilla.

There's also a [tiny sample-data fixture](./sample-data) (en-US + tr) with intentional bugs, for smoke-testing the scripts without cloning the whole 500 MB `firefox-l10n` repo.

## Related Mozilla tooling

[`compare-locales`](https://hg.mozilla.org/l10n/compare-locales/) is what Mozilla's CI actually uses for production audits. The scripts here re-implement small slices of its parsing logic to make the primitives explicit and to learn the AST. For production, prefer `compare-locales` with the repo's `l10n.toml` config — it handles edge cases the scripts here don't.

## License

[MIT](./LICENSE).
