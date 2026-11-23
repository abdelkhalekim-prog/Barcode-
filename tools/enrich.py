#!/usr/bin/env python3
"""Fetch price / express flag / image for Nahdi items from their public product pages.
Usage: enrich.py data.pack sitemap_skus.json out.jsonl [workers]
Resumable: skips SKUs already in out.jsonl. Missing-price items go first.
"""
import sys, json, gzip, re, time, urllib.request, concurrent.futures as cf, threading

pack, skus_file, out = sys.argv[1], sys.argv[2], sys.argv[3]
workers = int(sys.argv[4]) if len(sys.argv) > 4 else 5
budget = float(sys.argv[5]) * 60 if len(sys.argv) > 5 else 1e12  # minutes
d = json.loads(gzip.open(pack).read())
online = set(json.load(open(skus_file)))
done = set()
try:
    for line in open(out, encoding='utf-8'):
        done.add(json.loads(line)['s'])
except FileNotFoundError:
    pass

def noprice(x):
    try: return float(x[3] or 0) == 0
    except ValueError: return True

todo = [x[0] for x in d['items'] if x[0] in online and x[0] not in done]
np_codes = {x[0] for x in d['items'] if noprice(x)}
todo.sort(key=lambda s: 0 if s in np_codes else 1)
print('todo', len(todo), 'noprice first', len([s for s in todo if s in np_codes]), flush=True)

UA = 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36'
lock = threading.Lock()
t0 = time.time()
fo = open(out, 'a', encoding='utf-8')

def fetch(sku):
    if time.time() - t0 > budget:
        return None
    url = f'https://www.nahdionline.com/ar-sa/x/pdp/{sku}'
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Encoding': 'gzip'})
            with urllib.request.urlopen(req, timeout=40) as r:
                raw = r.read()
                if r.headers.get('Content-Encoding') == 'gzip':
                    raw = gzip.decompress(raw)
            h = raw.decode('utf-8', 'ignore')
            rec = {'s': sku}
            m = re.search(r'"priceCurrency":"SAR","price":([0-9.]+)', h)
            if m: rec['p'] = float(m.group(1))
            else:
                m = re.search(r'"priceCurrency":"SAR","lowPrice":([0-9.]+),"highPrice":([0-9.]+)', h)
                if m:
                    lo, hi = float(m.group(1)), float(m.group(2))
                    rec['p'] = hi
                    if lo < hi: rec['d'] = lo
            m = re.search(r'global_filter_label\\?":\\?"(\w+)', h)
            if m: rec['g'] = m.group(1)
            if 'schema.org/OutOfStock' in h: rec['o'] = 1
            return rec
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return {'s': sku, 'x': e.code}
            time.sleep(2 + attempt * 3)
        except Exception:
            time.sleep(2 + attempt * 3)
    return None

n = 0
with cf.ThreadPoolExecutor(workers) as ex:
    for rec in ex.map(fetch, todo):
        if rec is None: continue
        with lock:
            fo.write(json.dumps(rec, ensure_ascii=False) + '\n'); n += 1
            if n % 200 == 0:
                fo.flush(); print(n, f'{n/(time.time()-t0):.1f}/s', flush=True)
fo.close(); print('done', n)
