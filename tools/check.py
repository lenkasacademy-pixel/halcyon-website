#!/usr/bin/env python3
"""Pre-publish checks for the Halcyon site. Run from anywhere: python3 tools/check.py

Fails (exit 1) on anything a search engine or a visitor would trip over: broken internal
links or #anchors, JSON-LD that does not parse or points at an @id that does not exist,
missing/duplicate titles and descriptions, pages without exactly one <h1>, images without
alt text or dimensions, and sitemap URLs that do not resolve to a page.
"""
import glob, html, json, os, re, sys
from urllib.parse import urljoin, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
DOMAIN = 'https://halcyonpainfree.com/'
errors, warns = [], []

def is_stub(s):
    return 'http-equiv="refresh"' in s

# Pages carried over from the old WordPress site that we host but do not own:
# the Meta ad landing pages and their leftovers. They are deployed so the ads
# keep working, but they are not part of this site and are not held to its
# rules — no canonical, no schema, no Open Graph. Do not "fix" them here.
CARRIED = {'7272.html', '7788.html', '8585.html', 'home.html', '404.shtml'}

pages = {}
for f in sorted(glob.glob('**/*.html', recursive=True)):
    if f.startswith(('tools/', 'node_modules/')) or f in CARRIED:
        continue
    pages[f] = open(f, encoding='utf-8').read()

def url_of(f):
    return '' if f == 'index.html' else (f[:-len('index.html')] if f.endswith('/index.html') else f)

def resolve(from_file, href):
    base = 'http://x/' + url_of(from_file)
    u = urlparse(urljoin(base, href))
    path = u.path.lstrip('/')
    if path == '' or path.endswith('/'):
        target = path + 'index.html'
    else:
        target = path
    return target, u.fragment

ids = {f: set(re.findall(r'\sid="([^"]+)"', s)) for f, s in pages.items()}
titles, descs = {}, {}
all_ld_ids = set()
page_ld = {}

for f, s in pages.items():
    stub = is_stub(s)
    # ---- links
    for href in re.findall(r'\shref="([^"]+)"', s):
        if href.startswith(('http:', 'https:', 'tel:', 'mailto:', 'data:', 'javascript:')) or href.startswith('#bird'):
            continue
        if f == '404.html' and href.startswith('/'):
            continue  # served from any depth; root-relative on purpose
        tgt, frag = resolve(f, href)
        if not os.path.exists(tgt):
            errors.append('%s: broken link %s' % (f, href)); continue
        if frag and tgt.endswith('.html') and frag not in ids.get(tgt, set()):
            errors.append('%s: missing anchor %s' % (f, href))
    for src in re.findall(r'\ssrc="([^"]+)"', s):
        if src.startswith(('http', 'data:')):
            continue
        tgt, _ = resolve(f, src)
        if not os.path.exists(tgt):
            errors.append('%s: missing file %s' % (f, src))
    for src in re.findall(r"url\((?:'|\")?([^)'\"]+)", s):
        if src.startswith(('http', 'data:', '#')):
            continue
        if not os.path.exists(resolve(f, src)[0]):
            errors.append('%s: missing css url %s' % (f, src))
    if stub:
        continue
    # ---- head
    t = re.search(r'<title>(.*?)</title>', s, re.S)
    d = re.search(r'<meta name="description" content="([^"]*)"', s)
    noindex = 'content="noindex' in s
    if not t:
        errors.append('%s: no <title>' % f)
    elif not noindex and f != '404.html':
        tt = html.unescape(t.group(1).strip())
        if len(tt) > 65: warns.append('%s: title %d chars' % (f, len(tt)))
        titles.setdefault(tt, []).append(f)
    if not noindex and f != '404.html':
        if not d:
            errors.append('%s: no meta description' % f)
        else:
            dd = html.unescape(d.group(1))
            if not 110 <= len(dd) <= 165: warns.append('%s: description %d chars' % (f, len(dd)))
            descs.setdefault(dd, []).append(f)
        for need in ('rel="canonical"', 'property="og:image"', 'name="twitter:card"', 'application/ld+json'):
            if need not in s:
                errors.append('%s: missing %s' % (f, need))
        c = re.search(r'<link rel="canonical" href="([^"]+)"', s)
        if c and c.group(1) != DOMAIN + url_of(f):
            errors.append('%s: canonical %s != %s' % (f, c.group(1), DOMAIN + url_of(f)))
    h1 = len(re.findall(r'<h1[\s>]', s))
    if h1 != 1 and not noindex:
        errors.append('%s: %d <h1>' % (f, h1))
    # ---- images
    body = s[s.find('<body'):]
    for tag in re.findall(r'<img\b[^>]*>', body):
        if 'alt=' not in tag:
            errors.append('%s: img without alt %s' % (f, tag[:90]))
        if 'width=' not in tag or 'height=' not in tag:
            warns.append('%s: img without dimensions %s' % (f, tag[:90]))
    # ---- json-ld
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            data = json.loads(block)
        except Exception as e:
            errors.append('%s: JSON-LD does not parse: %s' % (f, e)); continue
        nodes = data.get('@graph', [data])
        own = {n.get('@id') for n in nodes if n.get('@id')}
        all_ld_ids.update(own)
        refs = set()
        def walk(o):
            if isinstance(o, dict):
                if set(o) == {'@id'}:
                    refs.add(o['@id'])
                for v in o.values(): walk(v)
            elif isinstance(o, list):
                for v in o: walk(v)
        walk(nodes)
        page_ld[f] = (own, refs)
        for n in nodes:
            if n.get('@type') == 'FAQPage':
                for q in n['mainEntity']:
                    if html.escape(q['name'], quote=False) not in s and q['name'] not in html.unescape(s):
                        errors.append('%s: FAQ question not visible on page: %s' % (f, q['name']))

for f, (own, refs) in page_ld.items():
    for r in refs - own:
        # a reference to another page's node is fine as long as that page defines it
        if r not in all_ld_ids:
            errors.append('%s: JSON-LD @id %s is defined nowhere' % (f, r))

for t, fs in titles.items():
    if len(fs) > 1: errors.append('duplicate title "%s": %s' % (t, fs))
for d, fs in descs.items():
    if len(fs) > 1: errors.append('duplicate description: %s' % fs)

# ---- sitemap
if os.path.exists('sitemap.xml'):
    sm = open('sitemap.xml').read()
    for loc in re.findall(r'<url><loc>([^<]+)</loc>', sm):
        rel = loc[len(DOMAIN):]
        tgt = (rel + 'index.html') if rel == '' or rel.endswith('/') else rel
        if not os.path.exists(tgt): errors.append('sitemap: %s has no file' % loc)
        elif is_stub(open(tgt).read()): errors.append('sitemap: %s is a redirect' % loc)
        elif 'content="noindex' in open(tgt).read(): errors.append('sitemap: %s is noindex' % loc)
else:
    errors.append('no sitemap.xml')
for f in ('robots.txt', 'llms.txt', 'llms-full.txt', 'site.webmanifest', 'favicon.ico', '404.html'):
    if not os.path.exists(f): errors.append('missing %s' % f)

for w in warns: print('warn ', w)
for e in errors: print('ERROR', e)
print('%d pages checked · %d errors · %d warnings' % (len(pages), len(errors), len(warns)))
sys.exit(1 if errors else 0)
