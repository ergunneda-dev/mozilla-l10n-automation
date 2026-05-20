# Sample data

Two tiny Fluent files for smoke-testing the scripts before pointing them at the real `firefox-l10n` checkout.

The Turkish file has intentional bugs:
- `new-tab-button.tooltiptext` is missing entirely → `audit_missing.py` should flag it
- `welcome-banner` is missing the `$name` placeable → `check_placeables.py` should flag it
- `settings-saved` has an empty value → both `audit_missing.py` and `completeness_report.py` should count it

Quick run:

```bash
pip install --break-system-packages fluent.syntax
cd ../scripts

python audit_missing.py     ../sample-data/en-US ../sample-data/tr
python check_placeables.py  ../sample-data/en-US ../sample-data/tr
python completeness_report.py ../sample-data
python bulk_rename.py       ../sample-data "Firefox" "Mozilla Firefox"
```

The last command is dry-run by default — add `--apply` once you've reviewed the preview.
