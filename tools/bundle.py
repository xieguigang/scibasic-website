#!/usr/bin/env python3
"""Bundle the modular src/ into a single self-contained index.html.

The platform delivery extracts the entry HTML file alone, so every asset
must be inlined: CSS -> <style>, module JS -> <script type="module">,
images -> base64 data URIs. Only three.js (importmap CDN) stays external.
"""
import base64, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'

html = (SRC / 'index.html').read_text(encoding='utf-8')
css = (SRC / 'style.css').read_text(encoding='utf-8')
main = (SRC / 'main.js').read_text(encoding='utf-8')
shape = (SRC / 'penrose-shape.js').read_text(encoding='utf-8')

knot_b64 = base64.b64encode((SRC / 'logo-knot.png').read_bytes()).decode()

# 1) stylesheet -> inline <style>
html = html.replace(
    '<link rel="stylesheet" href="assets/css/style.css" />',
    '<style>\n' + css + '\n</style>')

# 2) favicon + <img> references -> data URI
knot_uri = 'data:image/png;base64,' + knot_b64
html = html.replace('assets/img/logo-knot.png', knot_uri)

# 3) module script -> single inline module (drop local import, prepend shape data)
if "import { PENROSE } from './penrose-shape.js';" in main:
    main = main.replace("import { PENROSE } from './penrose-shape.js';",
                        '/* traced Penrose outline (was penrose-shape.js) */\n' +
                        shape.split('*/', 1)[1].strip())
assert '<script type="module" src="assets/js/main.js"></script>' in html
html = html.replace(
    '<script type="module" src="assets/js/main.js"></script>',
    '<script type="module">\n' + main + '\n</script>')

# 4) sanity: no local asset refs left
leftover = re.findall(r'(?:src|href)="assets/[^"]*"', html)
assert not leftover, f'unresolved local refs: {leftover}'

out = ROOT / 'index.html'
out.write_text(html, encoding='utf-8')
print(f'bundle written: {out} ({out.stat().st_size/1024:.0f} KB)')
