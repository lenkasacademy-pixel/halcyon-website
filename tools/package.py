#!/usr/bin/env python3
"""Make the upload bundle for a normal web host (GoDaddy cPanel, or any Apache).

    python3 tools/build.py && python3 tools/package.py

Writes dist/halcyon-site.zip containing exactly what belongs in public_html —
the pages, assets, .htaccess, sitemap, robots.txt — and nothing else (no git
history, no tools, no content sources). Unzipping it in public_html is the
whole deployment.
"""
import os, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SKIP_DIRS = {'.git', 'tools', 'dist', 'node_modules', '.github'}
SKIP_FILES = {'.DS_Store', '.gitignore', 'README.md'}

os.makedirs('dist', exist_ok=True)
out = 'dist/halcyon-site.zip'
n = 0
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for base, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
        for f in files:
            if f in SKIP_FILES or f.endswith(('.pyc', '.swp')):
                continue
            path = os.path.normpath(os.path.join(base, f))
            if path.startswith(('tools/', 'dist/')):
                continue
            z.write(path, path)
            n += 1
size = os.path.getsize(out) / 1e6
print('%s — %d files, %.1f MB' % (out, n, size))
print('Upload it to public_html and use cPanel File Manager → Extract.')
