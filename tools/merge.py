#!/usr/bin/env python3
"""Put this week's records over last week's: merge.py online.jsonl new.jsonl
Items the crawl did not reach this time keep their last known data."""
import sys, json

old, new = sys.argv[1], sys.argv[2]
recs = {}
for f in (old, new):
    try:
        for line in open(f, encoding='utf-8'):
            r = json.loads(line)
            recs[r['s']] = r
    except FileNotFoundError:
        pass
with open(old, 'w', encoding='utf-8') as fo:
    for r in recs.values():
        fo.write(json.dumps(r, ensure_ascii=False) + '\n')
print('records', len(recs))
