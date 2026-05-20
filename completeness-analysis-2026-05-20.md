# Completeness report — 2026-05-20

Scan of every locale in `firefox-l10n` against the canonical en-US source from [`mozilla-l10n/firefox-l10n-source`](https://github.com/mozilla-l10n/firefox-l10n-source) (11,927 messages total). Raw data: `l10n-completeness-2026-05-20.csv` in the same folder.

157 locales scanned. No parse errors anywhere — the entire repo is syntactically valid Fluent.

## Distribution

| Bucket | Count | Locales |
|---|---:|---|
| 100% complete | 19 | de, dsb, en-GB, es-CL, es-MX, fy-NL, hsb, ia, it, ka, ko, nl, nn-NO, ru, sr, sv-SE, th, tr, zh-TW |
| 95–99.99% | ~22 | fr, kk, nb-NO, cy, es-ES, eu, sk, el, es-AR, zh-CN, pt-BR, be, cs, hu, eo, pl, vi, ja, ja-JP-mac, ro, en-CA, gn, pt-PT, fi, sl, da, tg, pa-IN, he, sq |
| 90–95% | ~5 | uk, hr, fur, ar, rm |
| 50–90% | ~22 | id, gl, bs, is, hy-AM, kab, ca, sc, skr, oc, sat, bg, gd, br, lv, ml, cak, fa, et, si, lt, hye, tl, lo, bn, ca-valencia |
| 25–50% | ~28 | szl, sco, te, ur, hi-IN, an, mk, as, lij, trs, km, ast, mr, ne-NP, ff, gu-IN, az, ach, ga-IE, uz, bqi, crh, ms, bn-BD, ltg, ta, my, bn-IN, ckb, kn, brx, meh, mai, son |
| <25% | ~60 | af, or, xh, en-ZA, scn, ks, kok, csb, lg, ku, ak, sw, wo, nso, zu, bo, mn, sah, ixl, tn, zam, ace, ilo, lb, mix, rw, nr, st, ts, ve, tsz, frp, hto, ss, pbb, ta-LK, xcl, quy, ny, pai, gv, qvi, ppl |

## Highlights

**Nineteen at 100%.** The headliner. Includes the obvious heavyweights (de, ru, ko, sv-SE, it, nl) but also striking outliers like `dsb` (Lower Sorbian, ~7k speakers worldwide), `hsb` (Upper Sorbian), and `ia` (Interlingua, constructed). Those reflect tiny but extraordinarily dedicated translator communities — a fact you only see when you actually count. (en-GB is also in the set; it scores 100% trivially since its Fluent structure is identical to en-US — only the literal text differs. Worth knowing but not the most interesting datum.)

**fr and kk are at 99.99% — each missing exactly one string.** Clean targets for a "find and finish" task: identify the one string each, file a small bug, hit 100%. Worth knowing because it tells you the translator teams are still actively maintaining, not abandoned.

**Japanese at 98.78% confirms the placeable-audit story.** The 146 missing strings concentrate in `contextual-manager`, `genai`, `pdfviewer`, `link-preview`, and `aboutLogins` — all recently-landed Firefox features. `ja-JP-mac` is identical at 98.78% (it's the Mac-specific variant of `ja` and almost always tracks the main locale).

**Mid-tier anomaly: Catalan (`ca`) at 78.93%.** Notable because the other Romance locales are 99.76–100%: es-ES 99.92%, fr 99.99%, it 100%, pt-BR 99.76%. Catalan being 2,513 strings behind suggests either a translator gap or an overdue sync. Worth digging into.

**Long-tail observations.** Below 30% sits a mix of (a) actively-onboarded indigenous languages of the Americas (`zam`, `meh`, `trs`, `ixl`, `mix`, `cak`, `hto`, `pbb`, `ppl`, `quy`, `qvi`), (b) regional and minority European languages (`scn`, `csb`, `frp`, `lij`, `gv`, `sah`), and (c) several Asian languages still building up (`mai`, `kok`, `or`, `as`). The bottom rows — `ppl` 0.34%, `qvi` 0.61%, `gv` 0.71% — are essentially just-onboarded locales.

## Action items by bucket

| Bucket | Realistic ask |
|---|---|
| 100% | Maintenance only — keep tracking new strings as they land upstream. |
| 99–99.99% | "Push to 100%" sprint — small enough to be one ticket per locale. |
| 90–99% | Normal translation cycle — translators are active, just lagging the latest features. |
| 50–90% | Larger backlog, but locale is real. Coordinate with l10n team on priorities. |
| 25–50% | Translation onboarding zone. Quality more important than completeness here. |
| <25% | New / nascent locales. Don't measure these against the top tier — they're a different kind of effort. |

## Method notes

- Reference: en-US from [`mozilla-l10n/firefox-l10n-source`](https://github.com/mozilla-l10n/firefox-l10n-source) (11,927 messages). `firefox-l10n` itself holds only translations; Mozilla auto-syncs the canonical en-US source into the separate `firefox-l10n-source` repo from `mozilla-central`.
- A message counts as "translated" if it exists in the locale AND has either a value or an attribute. "Empty" means the entry exists but has neither (rare in practice — zero across all 157 locales in this run).
- Re-running this weekly is the natural cadence. The included `weekly-completeness.yml` GitHub Action does exactly that.
