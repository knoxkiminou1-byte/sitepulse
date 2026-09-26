# SitePulse — Website Health Audit Engine

**URL in → technical report + client-facing report out.**

SitePulse crawls any public website (up to N pages) and checks 20+ things across
security, SEO basics, accessibility structure, links, metadata, forms, and
conversion surface. Every finding ships with two views: a **technical** view
(evidence + detail, for whoever fixes it) and a **client** view (problem / why
it matters / the fix, in plain language, for the business owner).

It is strictly **read-only**: it fetches public pages, never posts, never
modifies anything on the target site.

## Quickstart

```bash
pip install -r requirements.txt
python3 audit.py https://example.com --pages 6 --out output
```

Output lands in `output/<domain>-<timestamp>/`:

| File | What it is |
|---|---|
| `report.json` | Machine-readable findings — feed it to other tools, dashboards, CRMs |
| `CLIENT-REPORT.md` | Plain-language report for the business owner, ends with a next-step CTA |
| `TECHNICAL-REPORT.md` | Developer-facing findings with evidence |

Example run:

```
$ python3 audit.py https://example.com --pages 6
Score: 70/100 (Grade C) · critical=0 warning=6 info=12 · 4 pages in 23.3s
Reports: output/example.com-20260926-164918/
```

## What it checks

- **Transport:** HTTPS, HSTS header, mixed content
- **Indexability:** meta robots / X-Robots-Tag noindex
- **SEO basics:** title tag (+length), meta description (+length), headings (H1 count, skipped levels), canonical URL, robots.txt, XML sitemap
- **Social/sharing:** Open Graph tags, structured data (JSON-LD)
- **Accessibility structure:** image alt text, form labels, `lang` attribute, viewport, charset
- **Links:** broken internal links (homepage, up to 25 checked — confirmed with GET before flagging)
- **Conversion:** call-to-action detection (book, call, contact, get started…)
- **Weight/speed hints:** page weight, server response time *(labeled honestly as server-to-server measurements, not real browser timings)*

Findings are scored: **critical** −12, **warning** −5, starting from 100 → grade A–F.

## The business model

This tool is a sales engine, not just a script:

1. **Lead magnet** — run a free audit on a prospect's site, send them `CLIENT-REPORT.md`. It shows them exactly what's broken, in words they understand.
2. **Paid audit** — deeper crawl + human review pass.
3. **Paid fix** — the report *is* the scope of work. Fix what's listed, re-run the audit, show the score go up.
4. **Retainer** — re-run monthly. Score-over-time is the retention story.

`report.json` is machine-readable on purpose: plug it into a CRM, a dashboard,
or an outreach pipeline.

## Honest limitations

- Speed numbers are server-to-server fetches, not real browser timings — every report says so.
- Broken-link check covers up to 25 same-host links on the homepage only (cost control).
- No JavaScript rendering — JS-heavy pages may show fewer findings than a real browser would.
- No real accessibility-tree (axe) checks yet; current a11y coverage is structural.
- Checks are heuristic. The client report itself says a specialist should confirm critical items before delivery.

## Requirements

- Python 3.8+
- `requests` (the only dependency — HTML parsing is stdlib)

## License

MIT — see [LICENSE](LICENSE).
