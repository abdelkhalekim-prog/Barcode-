#!/usr/bin/env python3
"""Merge the item master with Nahdi Online data into data.pack (v2).
items: [code, en, ar, price, img, type, online_price, online_discount_price]
  type: 'e' express, 'g' global, '' unknown/not online
"""
import sys, json, gzip
src, imgf, onl, out = sys.argv[1:5]
slf = sys.argv[5] if len(sys.argv) > 5 else ''
sl = json.load(open(slf, encoding='utf-8')) if slf else {}
pmf = sys.argv[6] if len(sys.argv) > 6 else ''
pm = json.load(open(pmf)) if pmf else {}

def tier(x):
    # productmix.json holds only the level (3 = top, 2, 1); the monthly multiplier is never stored
    return x or 0
DIV = {'WELLNESS': 'صحة وعافية', 'BEAUTY': 'تجميل', 'PERSONAL CARE': 'عناية شخصية', 'MOM AND BABY': 'الأم والطفل', 'MEDICINE': 'أدوية'}
NOT_MEDICINE = {'BEAUTY', 'PERSONAL CARE', 'MOM AND BABY'}
cats, catix = [], {}
d = json.loads(gzip.open(src).read())
img = json.load(open(imgf))
PRE = 'https://ecombe.nahdionline.com/media/catalog/product/'
on = {}
for line in open(onl, encoding='utf-8'):
    r = json.loads(line); on[r['s']] = r
def num(v):
    return ('%g' % v) if isinstance(v, (int, float)) else ''
items = []
stats = dict(img=0, e=0, g=0, filled=0, vat=0, novat=0)
for it in d['items']:
    code, en, ar, price = it[:4]
    im = img.get(code, '')
    if im.startswith(PRE): im = im[len(PRE):]
    r = on.get(code, {})
    t = {'express': 'e', 'global': 'g'}.get(r.get('g', '').lower(), '')
    op = num(r.get('p')) if 'p' in r else ''
    dp = num(r.get('d')) if 'd' in r else ''
    try: has = float(price or 0) > 0
    except ValueError: has = False
    if not has and op: stats['filled'] += 1
    if im: stats['img'] += 1
    if t: stats[t] += 1
    # VAT: medicines are zero-rated, everything else 15%. The item file price is before VAT,
    # Nahdi Online's price includes it, so the ratio between them tells us which one it is.
    v = ''
    if has and 'p' in r:
        q = r['p'] / float(price)
        if abs(q - 1.15) < 0.012: v = 1
        elif abs(q - 1) < 0.006: v = 0
    brand, ci, isl = '', -1, 0
    if code in sl:
        b, div, cat, sub = sl[code]
        brand, isl = b, 1
        lab = DIV.get(div, div.title()) + '|' + ' › '.join(x.title() for x in (cat, sub) if x)
        if lab not in catix: catix[lab] = len(cats); cats.append(lab)
        ci = catix[lab]
        # the user confirmed: only medicines are VAT-free, so these divisions carry 15%
        if v == '' and div in NOT_MEDICINE: v = 1
    if v == 1: stats['vat'] += 1
    elif v == 0: stats['novat'] += 1
    tr = tier(pm.get(code))
    if tr: stats['pm%d' % tr] = stats.get('pm%d' % tr, 0) + 1
    items.append([code, en, ar, price if has else '', im, t, op, dp, v, brand, ci, isl, tr])
pack = {'v': 2, 'built': __import__('datetime').date.today().isoformat(), 'imgBase': PRE,
        'items': items, 'bc': d['bc'], 'cats': cats}
with gzip.open(out, 'wt', encoding='utf-8', compresslevel=9) as f:
    json.dump(pack, f, ensure_ascii=False, separators=(',', ':'))
print(stats, 'online records', len(on))
