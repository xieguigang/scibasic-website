#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the two self-contained tutorial pages (demo-kmeans.html / demo-cuda.html).

Everything is inlined: the demo sources (escaped + syntax highlighted),
the scatter PNG (base64 data URI), the result CSV (rendered as a preview
table) and the CUDA console log (terminal-styled). No external assets
except the Inter webfont + three.js, same policy as the main page.
"""
import base64
import csv
import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'assets', 'demos')

MONO = "ui-monospace, 'Cascadia Mono', 'JetBrains Mono', Consolas, 'Courier New', monospace"

# ---------------------------------------------------------------- highlight
VB_KW = {
    'dim', 'redim', 'imports', 'call', 'using', 'end', 'sub', 'function', 'class',
    'module', 'structure', 'public', 'private', 'protected', 'friend', 'shared',
    'static', 'const', 'return', 'if', 'then', 'else', 'elseif', 'for', 'each',
    'next', 'to', 'step', 'while', 'do', 'loop', 'until', 'new', 'as', 'in',
    'try', 'catch', 'finally', 'throw', 'select', 'case', 'is', 'isnot', 'not',
    'and', 'andalso', 'or', 'orelse', 'mod', 'byval', 'byref', 'optional',
    'true', 'false', 'nothing', 'me', 'mybase', 'myclass', 'get', 'set',
    'implements', 'overrides', 'overloads', 'mustoverride', 'inheritable',
    'integer', 'single', 'double', 'string', 'boolean', 'long', 'object',
    'directcast', 'ctype', 'cint', 'csng', 'cdbl', 'cstr', 'cbool', 'clng',
}

def vb_tokens(src):
    """Tokenize VB/R# source into (kind, text); kind: kw|com|str|num|pre|op."""
    out, i, n = [], 0, len(src)
    line_start = True
    while i < n:
        c = src[i]
        if c == '\n':
            out.append(('tx', c)); i += 1; line_start = True; continue
        # preprocessor: #include / #r / #define at line start
        if line_start and c == '#':
            j = src.find('\n', i)
            if j < 0: j = n
            out.append(('pre', src[i:j])); i = j; continue
        if c == "'":                      # comment to EOL
            j = src.find('\n', i)
            if j < 0: j = n
            out.append(('com', src[i:j])); i = j; continue
        if c == '"':                      # string literal
            j = i + 1
            while j < n:
                if src[j] == '"':
                    if j + 1 < n and src[j + 1] == '"': j += 2; continue  # "" escape
                    j += 1; break
                j += 1
            out.append(('str', src[i:j])); i = j; continue
        if c.isalpha() or c == '_':
            j = i
            while j < n and (src[j].isalnum() or src[j] == '_'): j += 1
            word = src[i:j]
            out.append(('kw' if word.lower() in VB_KW else 'id', word)); i = j; continue
        if c.isdigit():
            j = i
            while j < n and (src[j].isalnum() or src[j] in '.+-' and
                             (src[j] in '+-' and src[j - 1] in 'eE' and j > i + 1)):
                if src[j] in '+-' and src[j - 1] not in 'eE': break
                j += 1
            out.append(('num', src[i:j])); i = j; continue
        out.append(('tx', c)); i += 1
        if not c.isspace(): line_start = False
    return out

def hl_vb(src):
    buf = []
    for kind, text in vb_tokens(src):
        t = html.escape(text)
        buf.append(t if kind in ('tx', 'id') else f'<span class="k-{kind}">{t}</span>')
    return ''.join(buf)

TERM_TITLE = re.compile(r'^(\s*)(=+|第 \d+ 步:.*|IL -> CUDA 教程:.*|-{4,}.*)$')

def hl_term(src):
    """Console log: dim the ==== rules, light up section titles and OK/FAIL."""
    lines = src.split('\n')
    out = []
    for ln in lines:
        e = html.escape(ln)
        if set(ln.strip()) <= {'='} and ln.strip():
            out.append(f'<span class="t-rule">{e}</span>')
        elif ln.strip().startswith('----') and ln.strip().endswith('----'):
            out.append(f'<span class="t-sub">{e}</span>')
        elif '第' in ln and ('步' in ln or '教程' in ln) and '====' not in ln:
            out.append(f'<span class="t-title">{e}</span>')
        elif ln.rstrip().endswith('OK'):
            head, _, tail = e.rpartition('OK')
            out.append(f'{head}<span class="t-ok">OK</span>')
        elif ln.rstrip().endswith('FAIL'):
            head, _, tail = e.rpartition('FAIL')
            out.append(f'{head}<span class="t-fail">FAIL</span>')
        elif ln.startswith('  已注册') or ln.startswith('  设备') or ln.startswith('  内核镜像'):
            out.append(f'<span class="t-hl">{e}</span>')
        else:
            out.append(e)
    return '\n'.join(out)

# ---------------------------------------------------------------- fragments
def read(name, binary=False):
    p = os.path.join(D, name)
    if binary:
        with open(p, 'rb') as f: return f.read()
    with open(p, encoding='utf-8-sig') as f: return f.read()

def csv_table(path, max_rows=12):
    with open(path, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    head, body = rows[0], rows[1:]
    def cell(ci, v):
        if head[ci] == 'class':
            return f'<span class="badge c{v}">{v}</span>'
        return html.escape(v)
    trs = ['<tr>' + ''.join(f'<th>{html.escape(h)}</th>' for h in head) + '</tr>']
    for r in body[:max_rows]:
        trs.append('<tr>' + ''.join(f'<td>{cell(i, v)}</td>' for i, v in enumerate(r)) + '</tr>')
    more = len(body) - max_rows
    if more > 0:
        trs.append(f'<tr class="more"><td colspan="{len(head)}">… {more} more rows in bezdekIris-pca-groups.csv</td></tr>')
    return '\n'.join(trs)

def png_uri(name):
    return 'data:image/png;base64,' + base64.b64encode(read(name, binary=True)).decode()

def split_cuda_sections(src):
    """Split cuda.vb at the three '第 N 节' banner comments."""
    marks = [m.start() for m in re.finditer(r"' -+\n'  第 \d+ 节", src)]
    marks.append(len(src))
    heads = ["Kernel functions — PearsonMetrics",
             "CPU reference & self-check — TutorialKit",
             "Main pipeline — translate, register, launch, verify"]
    out = []
    for k in range(3):
        out.append((heads[k], src[marks[k]:marks[k + 1]].rstrip() + '\n'))
    return out

# ---------------------------------------------------------------- template
CSS = """
:root{--bg:#030303;--ink:#eaeaea;--dim:#8a8f98;--faint:#565b63;--hairline:rgba(255,255,255,.14);
--hairline2:rgba(255,255,255,.07);--red:#ff3b2f;--panel:#0b0d10;}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--ink);font-family:Inter,-apple-system,'Segoe UI',sans-serif;
font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.mono{font-family:__MONO__}
/* top bar */
.topbar{position:fixed;inset:0 0 auto 0;z-index:50;display:flex;align-items:center;
justify-content:space-between;padding:18px 34px;background:linear-gradient(rgba(3,3,3,.92),rgba(3,3,3,.55) 70%,transparent)}
.brand{display:flex;align-items:center;gap:10px;font-size:14px;letter-spacing:.06em}
.brand img{width:20px;height:20px}
.topnav{display:flex;gap:26px;font-family:__MONO__;font-size:11px;letter-spacing:.12em;color:var(--dim)}
.topnav a:hover{color:var(--ink)}
/* hero */
.wrap{max-width:1060px;margin:0 auto;padding:0 34px}
.hero{padding:158px 0 30px;border-bottom:1px solid var(--hairline2)}
.kicker{font-family:__MONO__;font-size:11px;letter-spacing:.22em;color:var(--red)}
h1{font-size:clamp(30px,4.6vw,52px);font-weight:600;letter-spacing:-.02em;line-height:1.08;margin:14px 0 14px}
h1 .u{color:var(--dim);font-weight:400}
.lede{max-width:680px;color:var(--dim);font-size:15.5px}
.meta{display:flex;flex-wrap:wrap;gap:10px;margin-top:26px}
.meta div{border:1px solid var(--hairline);padding:8px 14px;font-family:__MONO__;font-size:10.5px;
letter-spacing:.1em;color:var(--dim);text-transform:uppercase}
.meta b{color:var(--ink);font-weight:500}
/* sections */
section{padding:58px 0;border-bottom:1px solid var(--hairline2)}
h2{font-family:__MONO__;font-size:11.5px;font-weight:500;letter-spacing:.24em;text-transform:uppercase;
color:var(--faint);margin-bottom:26px}
h2 em{font-style:normal;color:var(--red)}
/* code blocks */
.code{background:var(--panel);border:1px solid var(--hairline2);overflow-x:auto;
font-family:__MONO__;font-size:12.5px;line-height:1.62;padding:22px 24px;color:#c6cbd2;tab-size:4}
.code pre{white-space:pre}
.k-kw{color:#e8e8e8;font-weight:600}.k-com{color:#5d636c;font-style:italic}
.k-str{color:#c98f6d}.k-num{color:#7fb3a4}.k-pre{color:#b58bd8}
details{border:1px solid var(--hairline2);border-top:none}
details:first-of-type{border-top:1px solid var(--hairline2)}
summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:14px;
padding:14px 20px;font-family:__MONO__;font-size:12px;letter-spacing:.08em;color:var(--dim);
background:#08090b;user-select:none}
summary:hover{color:var(--ink)}
summary .arrow{color:var(--red);font-size:10px;transition:transform .25s}
details[open] .arrow{transform:rotate(90deg)}
details .code{border:none}
/* figure */
figure{margin:0}
figure img{display:block;width:100%;max-width:880px;border:1px solid var(--hairline2)}
figcaption{font-family:__MONO__;font-size:11px;letter-spacing:.1em;color:var(--faint);margin-top:12px}
/* table */
.tblwrap{border:1px solid var(--hairline2);overflow-x:auto;max-height:480px;overflow-y:auto}
table{border-collapse:collapse;width:100%;font-family:__MONO__;font-size:12px}
th{position:sticky;top:0;background:#101318;color:var(--dim);font-weight:500;letter-spacing:.08em;
text-align:left;padding:9px 16px;border-bottom:1px solid var(--hairline)}
td{padding:7px 16px;border-bottom:1px solid var(--hairline2);color:#b9bfc7;white-space:nowrap}
tr:hover td{background:#0d1014}
.badge{display:inline-block;min-width:20px;text-align:center;padding:0 6px;border:1px solid}
.badge.c1{color:#c0504d;border-color:#c0504d66}
.badge.c2{color:#4d84c0;border-color:#4d84c066}
.badge.c3{color:#7ba05b;border-color:#7ba05b66}
tr.more td{color:var(--faint);font-style:italic}
/* terminal */
.term{border:1px solid var(--hairline2);background:#050607}
.termbar{display:flex;align-items:center;gap:8px;padding:10px 16px;border-bottom:1px solid var(--hairline2);
font-family:__MONO__;font-size:10.5px;letter-spacing:.12em;color:var(--faint)}
.termbar i{width:8px;height:8px;background:#24282e;display:inline-block}
.termscroll{max-height:600px;overflow:auto;padding:20px 22px;font-family:__MONO__;font-size:12px;
line-height:1.6;color:#a9b0b8;white-space:pre}
.t-rule{color:#3a3f46}.t-title{color:#e4e7ea;font-weight:600}.t-sub{color:#c98f6d}
.t-ok{color:#7ec97e;font-weight:600}.t-fail{color:#ff6b6b;font-weight:600}.t-hl{color:#d9dee4}
/* prose */
.note{max-width:760px;color:var(--dim);font-size:14px}
.note b{color:var(--ink);font-weight:500}
.note code{font-family:__MONO__;font-size:12.5px;color:#c98f6d;background:#101216;padding:1px 6px}
/* pipeline */
.pipe{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-family:__MONO__;font-size:11.5px;margin:6px 0 4px}
.pipe span{border:1px solid var(--hairline);padding:8px 13px;color:var(--ink);background:#0b0d10}
.pipe i{color:var(--red);font-style:normal}
/* footer pager */
.pager{display:flex;justify-content:space-between;gap:20px;padding:44px 0 70px}
.pager a{flex:1;border:1px solid var(--hairline);padding:18px 20px;font-family:__MONO__;font-size:11px;
letter-spacing:.12em;color:var(--dim);text-transform:uppercase;transition:border-color .25s,color .25s}
.pager a:hover{border-color:rgba(255,255,255,.45);color:var(--ink)}
.pager a b{display:block;color:var(--ink);font-weight:500;font-size:13px;letter-spacing:.04em;
text-transform:none;margin-top:6px}
.pager a.nx{text-align:right}
.foot{padding:0 34px 40px;text-align:center;font-family:__MONO__;font-size:10.5px;
letter-spacing:.14em;color:var(--faint)}
.foot a{color:var(--dim)}.foot a:hover{color:var(--ink)}
@media(max-width:720px){.topbar{padding:14px 18px}.wrap{padding:0 18px}.hero{padding-top:120px}}
""".replace('__MONO__', MONO)

def page(title, desc, body, active):
    nav = f"""
<header class="topbar">
  <a class="brand" href="./"><strong>sciBASIC#</strong></a>
  <nav class="topnav">
    <a href="https://github.com/xieguigang/sciBASIC" target="_blank" rel="noopener">Library—</a>
    <a href="demo-kmeans.html"{' style="color:#eaeaea"' if active == 'km' else ''}>K-means demo</a>
    <a href="demo-cuda.html"{' style="color:#eaeaea"' if active == 'cu' else ''}>IL&rarr;CUDA demo</a>
  </nav>
</header>"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="color-scheme" content="dark" />
<meta name="description" content="{desc}" />
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
{nav}
<main class="wrap">
{body}
</main>
<div class="foot">sciBASIC# — a scientific computing stack in one language · <a href="./">scibasic.net</a> · GNU GPLv3</div>
</body>
</html>
"""

# ================================================================ kmeans page
def build_kmeans():
    script = hl_vb(read('kmeans.vb'))
    img = png_uri('bezdekIris-pca-groups.png')
    table = csv_table(os.path.join(D, 'bezdekIris-pca-groups.csv'))
    body = f"""
<div class="hero">
  <div class="kicker">TUTORIAL 01 / DATA MINING</div>
  <h1>K-means clustering,<br /><span class="u">then PCA — in one script</span></h1>
  <p class="lede">The classic Bezdek Iris benchmark: cluster 150 flowers by their four
  measurements, project them onto the first two principal components, draw the scatter
  plot and export the result table — all from a single R# script.</p>
  <div class="meta">
    <div>dataset <b>bezdekIris 150 × 4</b></div>
    <div>k <b>3</b></div>
    <div>script <b>35 lines</b></div>
    <div>run <b>vbs.exe kmeans.vb</b></div>
  </div>
</div>

<section>
  <h2><em>01</em> — The pipeline</h2>
  <div class="pipe">
    <span>bezdekIris.csv</span><i>→</i>
    <span>kmeans( k := 3 )</span><i>→</i>
    <span>PCA maxPC := 2</span><i>→</i>
    <span>ScatterPlot 800×600</span><i>→</i>
    <span>png + csv</span>
  </div>
  <p class="note">No hand-written loops anywhere: <b>data frame loading</b>, k-means,
  PCA and the publication-style plot all come from the framework — the script only
  wires them together. Drawing is powered by the <b>SkiaDriver</b> backend and the
  built-in <b>Nature</b> plot theme.</p>
</section>

<section>
  <h2><em>02</em> — The script · kmeans.vb</h2>
  <div class="code"><pre>{script}</pre></div>
</section>

<section>
  <h2><em>03</em> — Result · PCA scatter</h2>
  <figure>
    <img src="{img}" alt="PCA scatter of the Iris dataset, 3 cluster colours" />
    <figcaption>bezdekIris-pca-groups.png — 800 × 600, 300 dpi, PlotTheme.Nature().
    Setosa separates cleanly on PC1; versicolor / virginica split along PC2.</figcaption>
  </figure>
</section>

<section>
  <h2><em>04</em> — Result · exported table</h2>
  <p class="note" style="margin-bottom:20px">Every row keeps its original species in
  <code>ID</code> and carries the assigned cluster in <code>class</code> —
  <span class="badge c1">1</span> <span class="badge c2">2</span>
  <span class="badge c3">3</span> match the scatter colours.</p>
  <div class="tblwrap"><table>{table}</table></div>
</section>

<div class="pager">
  <a href="./"><b>← scibasic.net</b>Back to home</a>
  <a class="nx" href="demo-cuda.html"><b>IL → CUDA on the GPU →</b>Tutorial 02</a>
</div>
"""
    html_out = page('sciBASIC# — Tutorial: K-means + PCA on Iris',
                    'K-means clustering and PCA of the Bezdek Iris dataset in one R# script, with scatter plot and CSV export.',
                    body, 'km')
    with open(os.path.join(ROOT, 'demo-kmeans.html'), 'w', encoding='utf-8') as f:
        f.write(html_out)
    print('demo-kmeans.html written:', len(html_out), 'bytes')

# ================================================================ cuda page
def build_cuda():
    src = read('cuda.vb')
    sections = split_cuda_sections(src)
    details = []
    for i, (head, chunk) in enumerate(sections):
        op = ' open' if i == 0 else ''
        details.append(
            f'<details{op}><summary><span class="arrow">▶</span>'
            f'SECTION {i + 1} · {head.upper()}</summary>'
            f'<div class="code"><pre>{hl_vb(chunk)}</pre></div></details>')
    term = hl_term(read('stdout.txt'))
    body = f"""
<div class="hero">
  <div class="kicker">TUTORIAL 02 / GPU COMPUTING</div>
  <h1>IL &rarr; CUDA:<br /><span class="u">VB.NET functions compiled to the GPU</span></h1>
  <p class="lede">Six ordinary VB.NET math functions — no CUDA concepts anywhere — are
  decompiled from IL, rebuilt as an AST, emitted as <b>.cu</b> source, compiled at
  runtime by NVRTC and launched on the GPU to evaluate a 1024 × 1024 Pearson
  correlation matrix and Euclidean distance matrix.</p>
  <div class="meta">
    <div>matrix <b>1024 × 1024</b></div>
    <div>device <b>RTX A4000 · NVRTC 13.3 · sm_86</b></div>
    <div>max error <b>2.221E-007</b></div>
    <div>run <b>vbs.exe cuda.vb</b></div>
  </div>
</div>

<section>
  <h2><em>01</em> — How it works</h2>
  <div class="pipe">
    <span>VB.NET function</span><i>→</i>
    <span>IL bytecode</span><i>→</i>
    <span>AST</span><i>→</i>
    <span>.cu source</span><i>→</i>
    <span>NVRTC</span><i>→</i>
    <span>cuLaunchKernel</span>
  </div>
  <p class="note">Kernel shape is inferred from the parameter list, so you never write
  thread-index boilerplate: a parameter named <code>i</code> maps to a 1-D grid,
  <code>i</code> + <code>j</code> to a 2-D grid, and a pure-scalar function is wrapped
  element-wise automatically. After translation the same AST is replayed on a CPU
  interpreter and diffed against the original method as a self-check — every kernel
  in this tutorial reports <b>OK</b> before it ever touches the GPU.</p>
</section>

<section>
  <h2><em>02</em> — The script · cuda.vb (573 lines)</h2>
  {''.join(details)}
</section>

<section>
  <h2><em>03</em> — Console output · stdout.txt</h2>
  <div class="term">
    <div class="termbar"><i></i><i></i><i></i><span>VBS ENGINE — PearsonMetrics ON NVIDIA RTX A4000</span></div>
    <div class="termscroll">{term}</div>
  </div>
  <p class="note" style="margin-top:18px">The run finishes with
  <b>correlation error 2.221E-007</b> and <b>distance error 2.069E-005</b> against the
  double-precision CPU reference — pure single-precision GPU round-off, four to five
  orders of magnitude below the verification thresholds.</p>
</section>

<div class="pager">
  <a href="demo-kmeans.html"><b>← K-means + PCA</b>Tutorial 01</a>
  <a class="nx" href="./"><b>scibasic.net →</b>Back to home</a>
</div>
"""
    html_out = page('sciBASIC# — Tutorial: IL → CUDA, VB.NET on the GPU',
                    'Compile plain VB.NET math functions to CUDA kernels at runtime: IL decompilation, AST, NVRTC and GPU launch in one script.',
                    body, 'cu')
    with open(os.path.join(ROOT, 'demo-cuda.html'), 'w', encoding='utf-8') as f:
        f.write(html_out)
    print('demo-cuda.html written:', len(html_out), 'bytes')

if __name__ == '__main__':
    build_kmeans()
    build_cuda()
