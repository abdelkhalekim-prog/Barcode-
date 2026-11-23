#!/usr/bin/env python3
"""Read Nahdi Online's public sitemaps -> skus.json (SKUs on the site) + img.json (SKU -> image)."""
import re, json, time, urllib.request

UA = {'User-Agent': 'Mozilla/5.0'}

def get(url, t=180):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t).read().decode('utf-8', 'ignore')

idx = get('https://www.nahdionline.com/sitemap_index_ar.xml', 60)
img, skus = {}, set()
for loc in re.findall(r'<loc>([^<]+)</loc>', idx):
    h = get(loc)
    for u in re.findall(r'<url>(.*?)</url>', h, re.S):
        m = re.search(r'/pdp/(\d+)</loc>', u)
        if not m:
            continue
        s = m.group(1)
        skus.add(s)
        ims = re.findall(r'<image:loc>([^<]+)</image:loc>', u)
        if ims:
            img[s] = next((x for x in ims if 'small_image' in x), ims[0]).split('?')[0]
    time.sleep(1)
json.dump(sorted(skus), open('skus.json', 'w'))
# keep images from earlier runs when a sitemap leaves them out this week
try:
    old = json.load(open('img.json'))
except FileNotFoundError:
    old = {}
old.update(img)
json.dump(old, open('img.json', 'w'))
print('skus', len(skus), 'images', len(img))
