"""Figure: the six memory designs as block diagrams, PM-Bench style (boxes, arrows, one small table).
Six panels, 2 x 3. Every panel has the same bottom row (observation -> actor LLM -> action, looped);
what the store prepends sits above the actor. Run from aamas2027/:  python3 make_designs_fig.py
"""
import os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'figs')
W, H = 1000, 520
INK, MUTED = '#1c1c1c', '#5f5f5f'
PANEL = '#e8ebf2'
WHITE, LLM_F, LLM_S, ACT_F, ACT_S = '#ffffff', '#b9c8e6', '#3d5a8a', '#cdb08b', '#8a6b45'
STORE_F, STORE_S = '#ffffff', '#1c1c1c'
HARN_F, HARN_S = '#d9d9d9', '#6b6b6b'

svg = []
A = svg.append
A(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
  f'font-family="Helvetica, Arial, sans-serif">')
A('<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
  'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1c1c1c"/></marker></defs>')
A('<style>.t{font-size:14.5px;font-weight:700;fill:#1c1c1c}.b{font-size:11px;fill:#1c1c1c}'
  '.bb{font-size:11px;font-weight:700;fill:#1c1c1c}.m{font-size:9.6px;fill:#5f5f5f}'
  '.c{font-size:9.6px;fill:#1c1c1c;font-family:Menlo,Consolas,monospace}.w{fill:#ffffff}</style>')


def glyph(kind, x, y, c=INK):
    """small outline glyphs, one stroke style, centred at (x, y)"""
    g = f'<g transform="translate({x},{y})" fill="none" stroke="{c}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
    if kind == 'eye':
        g += '<path d="M-9,0 q9,-8 18,0 q-9,8 -18,0 z"/><circle cx="0" cy="0" r="2.6"/>'
    elif kind == 'robot':
        g += '<rect x="-8" y="-5" width="16" height="13" rx="3"/><circle cx="-3" cy="1.5" r="1.3" fill="%s" stroke="none"/><circle cx="3" cy="1.5" r="1.3" fill="%s" stroke="none"/><path d="M0,-5 v-4 M-2,-9 h4"/>' % (c, c)
    elif kind == 'bolt':
        g += '<path d="M2,-9 L-5,1 h5 L-2,9 L6,-1 h-5 z"/>'
    elif kind == 'doc':
        g += '<path d="M-6,-9 h8 l5,5 v13 h-13 z"/><path d="M2,-9 v5 h5 M-3,0 h7 M-3,4 h7"/>'
    elif kind == 'search':
        g += '<circle cx="-2" cy="-2" r="6"/><path d="M2.5,2.5 L8,8"/>'
    elif kind == 'pen':
        g += '<path d="M-8,8 l2,-6 l10,-10 l4,4 l-10,10 z"/><path d="M2,-6 l4,4"/>'
    elif kind == 'gear':
        g += '<circle cx="0" cy="0" r="3.2"/><path d="M0,-9 v3 M0,9 v-3 M-9,0 h3 M9,0 h-3 M-6.4,-6.4 l2.1,2.1 M6.4,6.4 l-2.1,-2.1 M-6.4,6.4 l2.1,-2.1 M6.4,-6.4 l-2.1,2.1"/>'
    elif kind == 'chat':
        g += '<path d="M-9,-7 h18 a2,2 0 0 1 2,2 v9 a2,2 0 0 1 -2,2 h-9 l-5,4 v-4 h-4 a2,2 0 0 1 -2,-2 v-9 a2,2 0 0 1 2,-2 z"/>'
    return g + '</g>'


def box(x, y, w, h, lines, fill=WHITE, stroke=INK, cls='b', rx=8, sw=1.6, dy=13.5, icon=None):
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    n = len(lines); y0 = y + h / 2 - (n - 1) * dy / 2 + 4
    if icon:      # glyph at the left, text left-aligned after it
        A(glyph(icon, x + 17, y + h / 2))
        for i, l in enumerate(lines):
            A(f'<text x="{x + 32}" y="{y0 + i * dy}" class="{cls if i == 0 else "m"}">{l}</text>')
    else:
        for i, l in enumerate(lines):
            A(f'<text x="{x + w / 2}" y="{y0 + i * dy}" class="{cls if i == 0 else "m"}" text-anchor="middle">{l}</text>')


def arrow(pts, dashed=False):
    d = ' '.join(('M' if i == 0 else 'L') + f'{x},{y}' for i, (x, y) in enumerate(pts))
    extra = ' stroke-dasharray="4,3"' if dashed else ''
    A(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="1.6"{extra} marker-end="url(#arr)"/>')


def cylinder(x, y, w, h, lines):
    ry = 7
    A(f'<path d="M{x},{y + ry} v{h - 2 * ry} a{w / 2},{ry} 0 0 0 {w},0 v{-(h - 2 * ry)}" fill="{WHITE}" stroke="{INK}" stroke-width="1.6"/>')
    A(f'<ellipse cx="{x + w / 2}" cy="{y + ry}" rx="{w / 2}" ry="{ry}" fill="{WHITE}" stroke="{INK}" stroke-width="1.6"/>')
    n = len(lines); y0 = y + ry + (h - ry) / 2 - (n - 1) * 6.5 + 4
    for i, l in enumerate(lines):
        A(f'<text x="{x + w / 2}" y="{y0 + i * 13}" class="b" text-anchor="middle">{l}</text>')


def table(x, y, rows, cw=(58, 68), rh=17):
    w = sum(cw)
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{rh * len(rows)}" fill="{WHITE}" stroke="{INK}" stroke-width="1.4"/>')
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{rh}" fill="#ececec" stroke="{INK}" stroke-width="1.4"/>')
    for i in range(1, len(rows)):
        A(f'<line x1="{x}" y1="{y + i * rh}" x2="{x + w}" y2="{y + i * rh}" stroke="{INK}" stroke-width="0.8"/>')
    A(f'<line x1="{x + cw[0]}" y1="{y}" x2="{x + cw[0]}" y2="{y + rh * len(rows)}" stroke="{INK}" stroke-width="0.8"/>')
    for i, (a, b) in enumerate(rows):
        cls = 'bb' if i == 0 else 'c'
        A(f'<text x="{x + cw[0] / 2}" y="{y + i * rh + 12}" class="{cls}" text-anchor="middle" font-size="9.6">{a}</text>')
        small = '' if i == 0 else ' style="font-size:9px"'
        A(f'<text x="{x + cw[0] + cw[1] / 2}" y="{y + i * rh + 12}" class="{cls}" text-anchor="middle"{small}>{b}</text>')


PW, PH = 318, 242
cols = [10, 341, 672]
rowsy = [10, 268]


def panel(px, py, title):
    A(f'<rect x="{px}" y="{py}" width="{PW}" height="{PH}" rx="14" fill="{PANEL}"/>')
    A(f'<text x="{px + PW / 2}" y="{py + 26}" class="t" text-anchor="middle">{title}</text>')


def bottom_row(px, py, loop=True):
    """observation -> actor -> action, with the action looping back to the observation. Returns key points."""
    by = py + PH - 96
    ox, ax, cx = px + 14, px + 130, px + 238
    box(ox, by, 96, 46, ['Observation', '+ last 6 steps'], icon='eye')
    box(ax, by, 90, 46, ['Actor LLM'], LLM_F, LLM_S, icon='robot')
    box(cx, by, 66, 46, ['Action'], ACT_F, ACT_S, icon='bolt')
    arrow([(ox + 96, by + 23), (ax, by + 23)])
    arrow([(ax + 90, by + 23), (cx, by + 23)])
    if loop:
        arrow([(cx + 33, by + 46), (cx + 33, by + 64), (ox + 48, by + 64), (ox + 48, by + 46)])
    return dict(by=by, ox=ox, ax=ax, cx=cx)


def store_arrow(px, p, label='prepended at every step'):
    """arrow from the store (above) into the actor"""
    ax = p['ax'] + 46
    arrow([(ax, p['by'] - 22), (ax, p['by'])])
    A(f'<text x="{ax + 6}" y="{p["by"] - 8}" class="m">{label}</text>')


def note(px, py, text):
    A(f'<text x="{px + PW / 2}" y="{py + PH - 9}" class="m" text-anchor="middle">{text}</text>')


# ---------- A. NONE ----------
px, py = cols[0], rowsy[0]
panel(px, py, 'A. NONE')
p = bottom_row(px, py)
A(f'<rect x="{px + 86}" y="{py + 50}" width="146" height="44" rx="8" fill="none" stroke="{MUTED}" stroke-width="1.4" stroke-dasharray="5,4"/>')
A(f'<text x="{px + PW / 2}" y="{py + 76}" class="m" text-anchor="middle">no store</text>')
note(px, py, 'the briefing leaves the window after 6 steps')

# ---------- B. BANK ----------
px, py = cols[1], rowsy[0]
panel(px, py, 'B. BANK (re-injected briefing)')
p = bottom_row(px, py)
box(px + 64, py + 50, 200, 58, ['Briefing, verbatim', 'chores + “if you notice the', 'Toaster is ON, turn it off”'], dy=13, icon='doc')
store_arrow(px, p)
note(px, py, 'never updated; the cancel message is only in the history')

# ---------- C. RETR ----------
px, py = cols[2], rowsy[0]
panel(px, py, 'C. RETR (lexical retrieval)')
p = bottom_row(px, py)
cylinder(px + 14, py + 48, 94, 62, ['All past', 'messages'])
box(px + 132, py + 56, 172, 46, ['Top-3 by lexical', 'match to the observation'], dy=13, icon='search')
arrow([(px + 108, py + 80), (px + 132, py + 80)])
arrow([(px + 218, py + 102), (px + 218, py + 112), (p['ax'] + 46, py + 112), (p['ax'] + 46, p['by'])])
A(f'<text x="{p["ax"] + 52}" y="{p["by"] - 8}" class="m">prepended</text>')
note(px, py, 'the cancel message is stored, but rarely retrieved')

# ---------- D. SUMM ----------
px, py = cols[0], rowsy[1]
panel(px, py, 'D. SUMM (rolling summary)')
p = bottom_row(px, py)
box(px + 14, py + 52, 128, 50, ['Summarizer LLM', 'every 6 steps'], LLM_F, LLM_S, icon='robot')
arrow([(px + 62, p['by']), (px + 62, py + 102)], dashed=True)
A(f'<text x="{px + 68}" y="{py + 126}" class="m">reads</text>')
box(px + 164, py + 52, 140, 50, ['Summary', 'free text, rewritten'], dy=13, icon='pen')
arrow([(px + 142, py + 77), (px + 164, py + 77)])
arrow([(px + 234, py + 102), (px + 234, py + 112), (p['ax'] + 46, py + 112), (p['ax'] + 46, p['by'])])
A(f'<text x="{p["ax"] + 52}" y="{p["by"] - 8}" class="m">prepended</text>')
note(px, py, 'the summary usually says “(cancelled)” and keeps the imperative')

# ---------- E. RWIM-LEDGER ----------
px, py = cols[1], rowsy[1]
panel(px, py, 'E. RWIM-LEDGER (self-kept ledger)')
p = bottom_row(px, py)
box(px + 14, py + 50, 136, 50, ['Bookkeeper LLM', 'same model, each step'], LLM_F, LLM_S, dy=13, icon='robot')
arrow([(px + 62, p['by']), (px + 62, py + 100)], dashed=True)
A(f'<text x="{px + 68}" y="{py + 126}" class="m">reads</text>')
table(px + 178, py + 46, [('trigger', 'status'), ('Toaster', 'CANCELLED'), ('Faucet', 'active')])
arrow([(px + 150, py + 75), (px + 178, py + 75)])
arrow([(px + 241, py + 97), (px + 241, py + 112), (p['ax'] + 46, py + 112), (p['ax'] + 46, p['by'])])
A(f'<text x="{p["ax"] + 52}" y="{p["by"] - 19}" class="m">+ task board (chores)</text>')
A(f'<text x="{p["ax"] + 52}" y="{p["by"] - 7}" class="m">rendered in fixed wording</text>')
note(px, py, 'reads the messages itself; no access to the true cancel step')

# ---------- F. SCHED ----------
px, py = cols[2], rowsy[1]
panel(px, py, 'F. SCHED (status-tracked, reference)')
p = bottom_row(px, py)
box(px + 14, py + 50, 136, 50, ['Harness (program)', 'status from cancel step'], HARN_F, HARN_S, dy=13, icon='gear')
table(px + 178, py + 46, [('trigger', 'status'), ('Toaster', 'CANCELLED'), ('Faucet', 'active')])
arrow([(px + 150, py + 75), (px + 178, py + 75)])
arrow([(px + 241, py + 97), (px + 241, py + 112), (p['ax'] + 46, py + 112), (p['ax'] + 46, p['by'])])
A(f'<text x="{p["ax"] + 52}" y="{p["by"] - 19}" class="m">+ task board (chores)</text>')
A(f'<text x="{p["ax"] + 52}" y="{p["by"] - 7}" class="m">rendered in fixed wording</text>')
note(px, py, 'same ledger as E, written from ground truth')

A('</svg>')
svg_text = '\n'.join(svg)
open(f'{OUT}/fig_designs.svg', 'w').write(svg_text)
html = (f'<!doctype html><html><head><meta charset="utf-8"><style>@page{{size:{W}px {H}px;margin:0}}'
        f'html,body{{margin:0;padding:0}}svg{{display:block}}</style></head><body>{svg_text}</body></html>')
hp = os.path.join(OUT, 'designs_tmp.html'); open(hp, 'w').write(html)
CH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
subprocess.run([CH, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={OUT}/fig_designs.pdf', 'file://' + hp], capture_output=True)
subprocess.run([CH, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--screenshot={OUT}/fig_designs.png',
                f'--window-size={W},{H}', '--force-device-scale-factor=4', 'file://' + hp], capture_output=True)
os.remove(hp)
print('written', f'{OUT}/fig_designs.svg / .pdf / .png')
