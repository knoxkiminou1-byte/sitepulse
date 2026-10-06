#!/usr/bin/env python3
"""Export a Sitepulse report.json to CSV. Evidence column is required."""
import csv, json, sys
from pathlib import Path

def findings_csv(findings, dest):
    fields = ['page', 'check', 'severity', 'title', 'evidence', 'why_it_matters', 'recommended_fix']
    with open(dest, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for row in findings:
            if not str(row.get('evidence') or '').strip():
                raise SystemExit('refusing a finding with no evidence')
            w.writerow(row)

def main():
    src = Path(sys.argv[1])
    data = json.loads(src.read_text())
    findings = data.get('findings') or data
    dest = src.with_suffix('.csv')
    findings_csv(findings, dest)
    print(dest)

if __name__ == '__main__':
    main()
