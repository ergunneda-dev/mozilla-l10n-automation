# Placeable audit — 2026-05-20

Run against `firefox-l10n` (HEAD at clone time), reference: canonical en-US source from [`mozilla-l10n/firefox-l10n-source`](https://github.com/mozilla-l10n/firefox-l10n-source). Six well-maintained locales sampled to gauge what `check_placeables.py` actually surfaces in practice.

Raw output: `placeables-multi-locale.txt` (in `~/code/firefox-l10n/`).

## Counts

| Locale | Issues | Reading |
|---|---:|---|
| de | 2 | clean |
| fr | 4 | clean |
| es-ES | 1 | clean |
| ja | **32** | outlier — investigate |
| zh-CN | 8 | mostly time/plural placeables |
| pt-BR | 3 | stale references only |

## The three categories every finding falls into

Not all "missing placeable" lines mean the same thing. Distinguishing them is the actual skill.

### Category 1 — deliberate simplifications (not bugs)

`-fxaccount-brand-name → ['$capitalization']` appears in **de, es-ES, ja, zh-CN, and tr** (5 of the 7 locales sampled). The en-US source has a `$capitalization` selector with `[sentence]` / `[title]` branches; translations collapsed both into a single form because their language doesn't need the English-style capitalization split. The source comment even gives translators permission: *"'Account' can be localized, 'Firefox' must be treated as a brand."*

No fix required. The script correctly flags the divergence, a human reviewer correctly concludes it's intentional.

### Category 2 — latent runtime UI bugs (probably real)

Pluralization placeables (`$count`, `$total`, `$tabCount`, `$timeValue`, `$rangePlural`, `$splitViewCount`) present in en-US but missing in the translation. At runtime, Firefox passes a number expecting substitution; the translation drops the variable; the user sees a sentence with no number (or a literal `{ $count }`).

Highest-confidence likely-bugs:

- **ja, password manager UI** — `about-logins-confirm-remove-all-dialog-message`, `contextual-manager-passwords-*`, `places-delete-*.label`, `lockwise-scanned-text-no-breached-logins`. "Delete N passwords / bookmarks" probably renders without the number in Japanese.
- **ja, tab context menus** — `tab-context-reopen-closed-tabs.label`, `tab-context-move-tabs.label`, `toolbar-context-menu-reopen-closed-tabs.label`. "Reopen N closed tabs" likely missing the count.
- **ja + zh-CN, download UI** — `downloadUtils.ftl` short-seconds/minutes/hours/days. The download-ETA labels likely render without the time value.
- **ja + zh-CN, PDF viewer** — `pdfjs-editor-comments-sidebar-title → ['$count']`. Probably renders without the comment count.

These are worth filing.

### Category 3 — stale references (cleanup, not crash)

`extra in translation:` lines: the translation references a variable or message that no longer exists in en-US. Fluent handles unknown references gracefully at runtime (it just substitutes nothing), so these don't crash. They're dead pointers that should be cleaned up when the locale next syncs.

- **ja, genai.ftl** — three `genai-chatbot-summarize-*-subtitle` entries reference `genai-menu-summarize-page`, which appears to have been renamed/removed in en-US.
- **fr, migrationWizard.ftl** — `migration-wizard-progress-success-bookmarks` references `$amount`, which seems no longer to be in the source.
- **pt-BR, unifiedExtensions.ftl** — three entries with `$extensionsCount` that the source no longer defines.

## Why Japanese is the outlier (32 vs ~3)

Look at *which* files Japanese is missing placeables in:

- `contextual-manager.ftl` — the new password manager UI
- `genai.ftl` — the GenAI chatbot sidebar
- `link-preview-reading-time` (genai + aboutReader) — recent link preview feature
- `pdfjs-editor-comments-sidebar-title` — PDF.js editor comments, a 2025/2026 addition

These are all **recent Firefox features**. The most likely explanation isn't that the Japanese team is sloppy — it's that en-US landed a lot of new strings in the last release cycle, and Japanese hasn't caught up to that wave yet. A normal pattern in l10n; would expect this to converge within a release or two.

The placeable check is also acting as a **leading indicator of translation freshness** for that reason. A locale's issue count spiking up correlates with new strings landing upstream that the locale hasn't picked up.

## What to do next

If this were a real l10n QA pass:

1. **File Category-2 findings as bugs** in Bugzilla (one per language, grouping by file). Tag the Japanese team for review.
2. **Open cleanup PRs for Category-3 findings.** They're low-risk because the references already don't resolve — removing them only tidies the file.
3. **Ignore Category-1 findings.** Optionally, document the convention so the next person running this script doesn't waste time re-investigating.
4. **Re-run in 4 weeks.** Watch whether the Japanese count drops as the team translates the new feature strings.

## Method notes

- Reference: canonical en-US source from [`mozilla-l10n/firefox-l10n-source`](https://github.com/mozilla-l10n/firefox-l10n-source). Mozilla auto-syncs this from `mozilla-central` so it's always the live source of truth for what landed upstream.
- All six locales sampled are well-maintained; the picture would look much noisier in smaller locales. Worth running across the full set (the `completeness_report.py` script does that).
