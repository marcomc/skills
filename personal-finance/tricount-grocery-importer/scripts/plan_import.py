#!/usr/bin/env python3
"""Plan receipt imports from normalized snapshots without network or mutations."""
import argparse
import json
from collections import defaultdict
from pathlib import Path


def plan(snapshot):
    """Prefer review over append whenever lines, aliases, or prior state exist."""
    sources = snapshot.get('sources', [])
    keys = [s['source_key'] for s in sources]
    if any(not k for k in keys) or len(keys) != len(set(keys)):
        raise ValueError('Source keys must be nonempty and unique')
    ledger = {}
    for row in snapshot.get('ledger', []):
        key = row['source_key']
        if key in ledger:
            raise ValueError('Duplicate ledger source key')
        ledger[key] = row
    lines_by_source, lines_by_legacy, receipt_owners = defaultdict(list), defaultdict(list), defaultdict(set)
    for index, row in enumerate(snapshot.get('existing_lines', [])):
        if row.get('source_key'):
            lines_by_source[row['source_key']].append(index)
        if row.get('legacy_transaction_id'):
            lines_by_legacy[row['legacy_transaction_id']].append(index)
        for key in row.get('receipt_keys', []):
            receipt_owners[key].add(row.get('source_key') or f'legacy-line:{index}')
    incoming_receipts = defaultdict(set)
    for source in sources:
        for receipt in source.get('receipt_keys', []):
            incoming_receipts[receipt].add(source['source_key'])
    result = []
    for source in sources:
        key = source['source_key']
        previous = ledger.get(key)
        present = set(lines_by_source[key])
        for alias in [source.get('upstream_id'), source.get('source_uuid')]:
            if alias:
                present.update(lines_by_legacy[alias])
        receipts = source.get('receipt_keys', [])
        collision = any(incoming_receipts[r] - {key} or receipt_owners[r] - {key} for r in receipts)
        changed = bool(previous and previous.get('fingerprint') and source.get('fingerprint')
                       and previous['fingerprint'] != source['fingerprint'])
        if collision:
            action, reason = 'review_receipt_link', 'Physical receipt already linked or shared by candidate sources'
        elif changed:
            action, reason = 'review_changed', 'Relevant source content changed; do not append a replacement receipt'
        elif present:
            if (previous and previous.get('state') == 'Importato verificato'
                    and source.get('fingerprint')
                    and previous.get('fingerprint') == source['fingerprint']):
                action, reason = 'skip', 'Verified unchanged receipt lines already present'
            else:
                action, reason = 'reconcile_existing', 'Existing rows found; resume or verify without full reimport'
        elif previous and previous.get('state') == 'Importato verificato':
            action, reason = 'review_missing_lines', 'Ledger says complete but no matching product rows exist'
        elif previous:
            action, reason = 'retry_pending', 'Prior attempt is not a completed product import'
        else:
            action, reason = 'new', 'No existing lines or ledger match; still verify receipt aliases before writing'
        result.append({'source_key': key, 'action': action, 'existing_line_count': len(present), 'reason': reason})
    # Deletions cannot disappear from the plan without a warning.
    for key in sorted(set(ledger) - set(keys)):
        if key.startswith('tricount:'):
            result.append({'source_key': key, 'action': 'review_absent_source',
                           'existing_line_count': len(lines_by_source[key]),
                           'reason': 'Absent from supplied upstream scope; verify scope/status, never delete automatically'})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = json.dumps(plan(json.loads(args.snapshot.read_text())), ensure_ascii=False, indent=2) + '\n'
    if args.out:
        args.out.write_text(result)
    else:
        print(result, end='')


if __name__ == '__main__':
    main()
