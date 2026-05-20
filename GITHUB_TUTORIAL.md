# Step-by-step: from zero to a merged PR (and a GitHub Action)

This guide takes you from "I have a GitHub account" to "I shipped a localization fix to mozilla-l10n and have a weekly automated report running in CI." Both paths — your local terminal and GitHub Codespaces — are covered side by side.

There are two big parts:

- **Part 1** — the manual contributor flow: fork, clone, branch, fix, push, PR.
- **Part 2** — automating it: run the same scripts on a schedule and on every PR via GitHub Actions.

---

## Part 0 · One-time setup

You said the account is ready but SSH and `gh` aren't set up. Do this once and you never touch it again.

### 0.1 Install the GitHub CLI (`gh`)

**macOS:**
```bash
brew install gh
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt update && sudo apt install gh
```

**Verify:**
```bash
gh --version
```

### 0.2 Authenticate `gh` (this also handles SSH for you)

```bash
gh auth login
```

Pick these answers at the prompts:
- **What account?** → GitHub.com
- **Preferred protocol?** → **SSH** (this is the important one — `gh` will generate and upload the SSH key for you, no manual `ssh-keygen` dance)
- **Generate a new SSH key?** → Yes (give it any title, e.g., "macbook-2026")
- **How to authenticate gh?** → Login with a web browser. Copy the one-time code it shows, paste it into the browser tab it opens, approve.

When it finishes, test:
```bash
ssh -T git@github.com
# expected: "Hi <your-username>! You've successfully authenticated..."
gh auth status
# expected: green check, "Logged in to github.com"
```

### 0.3 Set your git identity (if you've never done this)

```bash
git config --global user.name  "Eda Binen"
git config --global user.email "eda.binen@getyourguide.com"
```

Use the email that's verified on your GitHub account. If you'd rather not expose your real email, use GitHub's noreply address from Settings → Emails → "Keep my email address private."

### 0.4 Python toolkit (only needed locally; Codespaces has Python preinstalled)

```bash
python3 -m pip install --user fluent.syntax compare-locales
```

Verify:
```bash
python3 -c "import fluent.syntax; print('ok')"
```

That's all the one-time setup. Everything below is the repeatable workflow.

---

## Part 1 · The contributor flow

The model: you don't push directly to `mozilla-l10n/firefox-l10n`. You **fork** it (your own copy under your username), make changes on a **branch** in your fork, then open a **pull request** from your branch back to the upstream repo. Mozilla maintainers review and merge.

### Step 1 · Fork the repo

The fastest way is from your terminal — no clicking around:

```bash
gh repo fork mozilla-l10n/firefox-l10n --clone=false
```

This creates `<your-username>/firefox-l10n` under your account. The `--clone=false` flag means "fork but don't clone yet" — we'll clone explicitly in the next step so the upstream remote is wired correctly.

If you'd rather click: go to https://github.com/mozilla-l10n/firefox-l10n and hit the **Fork** button.

### Step 2 · Clone your fork

You have two ways to do this; pick one.

#### Option A · Local terminal

```bash
# adjust path to wherever you keep code
cd ~/code

gh repo clone <your-username>/firefox-l10n
cd firefox-l10n

# wire up the upstream remote so you can pull Mozilla's latest changes
git remote add upstream git@github.com:mozilla-l10n/firefox-l10n.git
git remote -v
# expected: origin = your fork, upstream = mozilla-l10n
```

> **Heads-up:** `firefox-l10n` is large (hundreds of locale directories). The clone can take several minutes. If you only care about a couple of locales, you can shallow-clone with `--depth=1` to speed it up: `gh repo clone <you>/firefox-l10n -- --depth=1`.

#### Option B · GitHub Codespaces

Codespaces gives you a full VS Code environment in the browser, pre-cloned and pre-configured.

1. On your fork's page (`github.com/<you>/firefox-l10n`), click the green **Code** button → **Codespaces** tab → **Create codespace on main**.
2. Wait ~30 seconds for the container to boot.
3. Open the integrated terminal (`Ctrl+`` ` or the menu).
4. Install the Python deps once per Codespace:
   ```bash
   pip install --user fluent.syntax compare-locales
   ```
5. The upstream remote isn't added automatically — do it once:
   ```bash
   git remote add upstream https://github.com/mozilla-l10n/firefox-l10n.git
   ```

The rest of the steps below work identically in both environments.

### Step 3 · Sync with upstream before you start

Always start a new piece of work from a fresh `main`:

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main          # keep your fork's main in sync too
```

### Step 4 · Create a branch for your change

Branch names should describe the work. Two patterns Mozilla uses a lot:
- `fix-<locale>-<area>` — e.g., `fix-tr-toolbar-placeables`
- `bulk-<change>` — e.g., `bulk-rename-firefox-account`

```bash
git checkout -b fix-tr-toolbar-placeables
```

### Step 5 · Run the audit scripts to find work

This is where the scripts from `scripts/` come in. They compare a locale to a reference — for `firefox-l10n` that reference lives in a separate repo, [`mozilla-l10n/firefox-l10n-source`](https://github.com/mozilla-l10n/firefox-l10n-source) (Mozilla auto-syncs the canonical en-US there from `mozilla-central`). Clone it once as a sibling of `firefox-l10n`:

```bash
cd ~/code
gh repo clone mozilla-l10n/firefox-l10n-source -- --depth=1
cd firefox-l10n
```

Now run the audits from inside `firefox-l10n`:

```bash
# What's missing or empty in Turkish?
python3 ~/mozilla-l10n-automation/scripts/audit_missing.py ../firefox-l10n-source tr

# What placeables are missing?
python3 ~/mozilla-l10n-automation/scripts/check_placeables.py ../firefox-l10n-source tr
```

Read the output. Each line tells you the file and message id you need to fix.

### Step 6 · Make the fix

For one-off fixes, just open the file in your editor and translate. For a bulk change (like the brand rename example), use `bulk_rename.py`:

```bash
# Preview first (dry-run is the default):
python3 ~/mozilla-l10n-automation/scripts/bulk_rename.py . "Firefox Account" "Mozilla account" --locales tr

# Looks right? Apply it:
python3 ~/mozilla-l10n-automation/scripts/bulk_rename.py . "Firefox Account" "Mozilla account" --locales tr --apply
```

### Step 7 · Review your changes with `git diff`

This is the single most important step. Translators have invested real work — `git diff` is your last chance to catch a regression before pushing.

```bash
git status            # what files changed
git diff              # what changed inside them
git diff --stat       # one-line summary per file
```

For a bulk change, scan every modified file. For a manual translation, you're mostly checking that you only edited what you meant to.

### Step 8 · Commit

```bash
git add tr/                                # stage just the locale dir you touched
git commit -m "tr: fix missing placeables in browser/toolbar.ftl"
```

Mozilla's commit-message convention is generally `<locale>: <what changed>`. Keep the subject line under ~70 characters; if you need more, add a blank line and a longer body explaining *why*.

### Step 9 · Push to your fork

```bash
git push -u origin fix-tr-toolbar-placeables
```

The `-u` sets the upstream tracking so future `git push` from this branch works without arguments.

### Step 10 · Open the pull request

From the terminal:
```bash
gh pr create --base main --head fix-tr-toolbar-placeables \
  --title "tr: fix missing placeables in browser/toolbar.ftl" \
  --body "Adds the \$count placeable to bookmarks-count and the \$name placeable to welcome-banner. Caught by check_placeables.py."
```

`gh` will print the PR URL when it's done. Open it to confirm everything looks right.

If you prefer the web UI: push the branch (step 9), then go to your fork's page on github.com — it'll show a yellow "Compare & pull request" banner. Click it, fill in the description, submit.

### Step 11 · Respond to review

Watch for review comments. To address them:

```bash
# make further edits, then:
git add <files>
git commit -m "address review: <what you changed>"
git push           # the PR updates automatically
```

Don't squash or force-push unless a maintainer asks you to — Mozilla reviewers generally prefer to see the history.

### Step 12 · After it merges, clean up

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
git branch -d fix-tr-toolbar-placeables     # local delete
git push origin --delete fix-tr-toolbar-placeables   # remote delete (optional)
```

That's the loop. Every change you ever ship to mozilla-l10n follows this pattern.

---

## Part 2 · GitHub Actions

The same scripts you ran by hand can run automatically — on a schedule, on every push, on every PR. The mechanism is **GitHub Actions**: YAML files in `.github/workflows/` that GitHub executes on its own runners.

Two example workflows live in `github-actions-examples/` next to this tutorial. Copy them into a real repo's `.github/workflows/` directory to activate.

### Where workflows live

```
<repo root>/
└── .github/
    └── workflows/
        ├── weekly-completeness.yml
        └── pr-placeable-check.yml
```

The `.github/workflows/` path is mandatory — that's how GitHub finds them. The filenames themselves don't matter.

### Anatomy of a workflow file

Every workflow has the same shape:

```yaml
name: Human-readable name shown in the Actions tab

on:                              # what triggers the run
  schedule: ...                  # cron
  pull_request: ...              # PR events
  push: ...                      # push events
  workflow_dispatch:             # manual "Run workflow" button

jobs:
  some-job-name:
    runs-on: ubuntu-latest       # the OS image GitHub gives you
    steps:
      - uses: actions/checkout@v4    # standard action: clones the repo
      - run: echo "your commands"    # arbitrary shell
```

### Example A · Weekly completeness report

`github-actions-examples/weekly-completeness.yml` runs every Monday at 06:00 UTC, executes `completeness_report.py`, and uploads the resulting CSV as a downloadable build artifact. Open the **Actions** tab in your repo to download it after each run.

You'd add this to a repo that contains both your scripts AND the locale data (or, more commonly, the workflow checks out two repos: yours-with-scripts and `firefox-l10n`).

### Example B · Per-PR placeable check

`github-actions-examples/pr-placeable-check.yml` runs on every pull request, computes which locales were touched by the PR's diff, runs `check_placeables.py` against each, and posts a sticky comment on the PR with the findings. If any locale has placeable mismatches, the job fails — so the PR gets a red ❌ and can be set up as a required check.

This is the highest-leverage Action you can run on a localization repo. It catches the kind of bug that breaks the UI at runtime, *before* the bad translation ever ships.

### Step-by-step: wire up an Action

1. In your fork (or any repo you control — testing in your own playground first is wise), create the directory:
   ```bash
   mkdir -p .github/workflows
   ```
2. Copy a workflow file in:
   ```bash
   cp ~/mozilla-l10n-automation/github-actions-examples/weekly-completeness.yml .github/workflows/
   ```
3. Commit and push:
   ```bash
   git add .github/workflows/weekly-completeness.yml
   git commit -m "ci: add weekly l10n completeness report"
   git push
   ```
4. Visit the **Actions** tab in your repo on github.com. You'll see the workflow listed. For scheduled workflows, the first run happens at the next cron tick; for the PR-check workflow, it runs on the next PR.
5. To trigger a scheduled workflow on-demand without waiting, click the workflow name → **Run workflow** button (this works because the example YAML includes `workflow_dispatch:`).

### Reading the run output

In the **Actions** tab, click into a run to see each step's logs. The completeness workflow's artifact appears at the bottom of the run summary page — click it to download the CSV.

### Permissions and secrets

You generally don't need any secrets for these workflows — they read public repos and use the auto-provided `GITHUB_TOKEN`. The PR-comment workflow *does* need write permissions on issues/PRs; that's declared in the YAML's `permissions:` block. Don't grant more than you need.

If you ever want a workflow to push commits back to a repo, you have two choices:
- Use the auto `GITHUB_TOKEN` (works for the same repo, with `permissions: contents: write`).
- Use a fine-grained personal access token stored as a repo secret if you need cross-repo writes.

### When NOT to automate

A few cases where it's better to keep things manual:
- **Pontoon-synced locales.** If Pontoon owns the locale, anything CI commits will likely be overwritten on the next sync.
- **Bulk rewrites at scale.** Doing a bulk rename in CI is tempting, but it leaves no human in the loop for the dry-run review. Better to run locally, eyeball the diff, then push the prepared PR.

Audit and reporting workflows are always safe; mutation workflows deserve a closer look.

---

## Cheat sheet

| Task | Command |
|---|---|
| Set up SSH + auth once | `gh auth login` (pick SSH, generate key) |
| Fork a repo | `gh repo fork mozilla-l10n/firefox-l10n` |
| Clone your fork | `gh repo clone <you>/firefox-l10n` |
| Sync your main with upstream | `git fetch upstream && git merge upstream/main` |
| New branch | `git checkout -b fix-<locale>-<area>` |
| Stage + commit | `git add <path> && git commit -m "<locale>: <what>"` |
| Push | `git push -u origin <branch>` |
| Open PR | `gh pr create --base main` |
| List your open PRs | `gh pr list --author @me` |
| Check Actions on a repo | github.com/<owner>/<repo>/actions |

---

## What to read next

- The four scripts in `scripts/` — they're heavily commented, treat them as a second tutorial in code form.
- Mozilla's contributor docs: https://mozilla-l10n.github.io/localizer-documentation/
- `compare-locales` docs: https://moz-l10n-config.readthedocs.io/
- GitHub Actions docs: https://docs.github.com/en/actions
