# Plan for a real upstream PR to mozilla-l10n/firefox-l10n

Companion to the [main README](./README.md) and the [practice PR](https://github.com/ergunneda-dev/firefox-l10n/pull/1) on my own fork. This document identifies specific, safe candidate fixes for a real upstream contribution and lays out the exact steps to submit one.

## Why "safe candidates" matter

Most placeable findings in the audit fall into one of three categories (see [the placeable audit](./placeable-audit-2026-05-20.md)). For a first upstream PR, **Category 3 — stale references** is the right starting point because:

- The fix is a *removal*, not a translation. No source-language knowledge required.
- The diff is small and verifiable.
- Risk is genuinely zero: the referenced variable already doesn't exist in en-US, so removing the reference cannot regress runtime behaviour.
- Reviewers can verify the fix in one glance.

## Candidate 1 (recommended): pt-BR unifiedExtensions stale refs

**Why this one:** three findings in a single file, same variable, single-locale scope.

**File:** `pt-BR/browser/browser/unifiedExtensions.ftl`

**Findings:**

```
extra in translation: unified-extensions-mb-blocklist-warning-multiple2.message  →  ['$extensionsCount']
extra in translation: unified-extensions-mb-blocklist-warning-multiple.message   →  ['$extensionsCount']
extra in translation: unified-extensions-mb-blocklist-error-multiple.message     →  ['$extensionsCount']
```

The pt-BR translation references `$extensionsCount` in three message attributes, but the en-US source no longer declares that variable for these messages. Either en-US simplified the strings, renamed the variable, or replaced these entries entirely. The investigation steps below figure out which, and the fix follows.

**Investigation steps:**

```bash
# Compare en-US and pt-BR for the same file, side by side.
diff ../firefox-l10n-source/browser/browser/unifiedExtensions.ftl \
     pt-BR/browser/browser/unifiedExtensions.ftl | less

# Or just look at the relevant section of en-US:
grep -A 5 "unified-extensions-mb-blocklist" ../firefox-l10n-source/browser/browser/unifiedExtensions.ftl
grep -A 5 "unified-extensions-mb-blocklist" pt-BR/browser/browser/unifiedExtensions.ftl
```

That tells you exactly what changed in en-US. Three likely outcomes:
1. **The messages were rewritten without `$extensionsCount`** → remove the `{ $extensionsCount }` placeable from each pt-BR entry; keep the surrounding text in Portuguese.
2. **The variable was renamed** (e.g., to `$count`) → update the placeable name in pt-BR.
3. **The messages were removed entirely** → remove these three entries from pt-BR too.

## Candidate 2: fr migrationWizard `$amount` stale ref

**File:** `fr/browser/browser/migrationWizard.ftl`

**Finding:**

```
extra in translation: migration-wizard-progress-success-bookmarks  →  ['$amount']
```

Single finding, similar pattern. Smaller PR (one line change) but requires French to keep the natural-sounding sentence after removing the variable. Skip if not comfortable in French.

## Candidate 3: ja genai stale message refs

**File:** `ja/browser/browser/genai.ftl`

**Findings:**

```
extra in translation: genai-chatbot-summarize-sidebar-provider-subtitle  →  ['genai-menu-summarize-page']
extra in translation: genai-chatbot-summarize-sidebar-generic-subtitle   →  ['genai-menu-summarize-page']
extra in translation: genai-chatbot-summarize-footer-provider-subtitle   →  ['genai-menu-summarize-page']
```

Three findings in one file. Different from the others: these are message references (no `$`), meaning the file references another message that was renamed/removed. Requires checking what `genai-menu-summarize-page` was replaced with in en-US, then updating the ja references accordingly. Slightly more involved but still doesn't require Japanese fluency.

## The submission workflow

The branch/commit/push pattern is identical to the practice PR. The two differences are:

1. The `gh pr create` command uses `--repo mozilla-l10n/firefox-l10n` instead of my own fork.
2. **No `--draft` flag** — a real upstream PR is open for review immediately.

Concretely, after making the fix and verifying with `git diff`:

```bash
# Start from a fresh branch off updated main
git checkout main
git fetch upstream
git merge upstream/main
git checkout -b fix-pt-br-unified-extensions-stale-refs

# Make the fix in pt-BR/browser/browser/unifiedExtensions.ftl
# ...verify with git diff and the Fluent parser...

git add pt-BR/browser/browser/unifiedExtensions.ftl
git commit -m 'pt-BR: remove stale $extensionsCount references in unifiedExtensions.ftl

en-US no longer declares $extensionsCount for these messages. Removing
the dead references in pt-BR brings the locale back in sync. Found by
check_placeables.py.'

git push -u origin fix-pt-br-unified-extensions-stale-refs

gh pr create \
  --repo mozilla-l10n/firefox-l10n \
  --base main \
  --head ergunneda-dev:fix-pt-br-unified-extensions-stale-refs \
  --title 'pt-BR: remove stale $extensionsCount references' \
  --body 'See body of commit message.'
```

The `--head ergunneda-dev:fix-...` syntax tells `gh` that the head branch lives in my fork, not Mozilla's.

## Before submitting

Read Mozilla's contributor expectations once:

- [mozilla-l10n contribution docs](https://mozilla-l10n.github.io/localizer-documentation/)
- The repo's [CODE_OF_CONDUCT.md](https://github.com/mozilla-l10n/firefox-l10n/blob/main/CODE_OF_CONDUCT.md)

Watch for these gotchas:

- **Pontoon sync.** If Pontoon owns the locale, GitHub-side fixes may be overwritten on the next sync. The Mozilla l10n team can confirm whether direct GitHub PRs are accepted for a given locale.
- **Locale ownership.** Some locales have specific maintainers who'd want a heads-up before a stranger pushes changes. Search the file's git blame and the l10n channel on Matrix/Slack.
- **One file at a time.** Even though the audit found dozens of findings, a focused first PR is more likely to merge than a sprawling one.

## Expected timeline

- **Day 0:** PR opens, CI runs (placeable check passes), maintainers see it.
- **Days 1–7:** Reviewer leaves comments or approves.
- **Days 2–14:** Locale-team member chimes in if there's a translation question.
- **Days 7–21:** Merge.

For a clean Category-3 cleanup, fast end is more likely.
