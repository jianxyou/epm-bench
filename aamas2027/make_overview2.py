"""Figure 1 (overview), panel style: three tinted panels with bold titles, real first-person frames,
little text. Frames come from figs/frames/*.png (recovered from the first version).
Run from aamas2027/:  python3 make_overview2.py
"""
import base64, os, subprocess
from overview_icons import (INK, MUTED, GRID, BASE, OR, BL, RED, GR, icon_person, icon_robot, icon_toaster,
                            icon_eye_off, icon_eye, icon_house, icon_note, icon_x, bubble)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'figs')
PA, PB, PC = '#eef3fb', '#fdf1e8', '#eaf6ee'          # panel tints
W, H = 1000, 330


def frame_b64(name):
    return base64.b64encode(open(f'{OUT}/frames/{name}.png', 'rb').read()).decode()


svg = []
A = svg.append
A(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
  f'font-family="Helvetica, Arial, sans-serif">')
A('<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
  'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#0b0b0b"/></marker>'
  '<marker id="arrg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
  'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#6f6e68"/></marker></defs>')
A('<style>.t{font-size:14px;font-weight:700;fill:#0b0b0b}.h{font-size:10.5px;font-weight:700;fill:#0b0b0b}'
  '.b{font-size:9.8px;fill:#0b0b0b}.m{font-size:9px;fill:#6f6e68}'
  '.c{font-size:9px;fill:#0b0b0b;font-family:Menlo,Consolas,monospace}'
  '.red{fill:#d03b3b}.blue{fill:#2a78d6}.or{fill:#eb6834}.gr{fill:#1baf7a}</style>')


def panel(x, y, w, h, fill, title, sub=None):
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}"/>')
    A(f'<text x="{x+12}" y="{y+21}" class="t">{title}</text>')
    if sub:
        A(f'<text x="{x+12}" y="{y+34}" class="m">{sub}</text>')


# ============ (a) one episode ============
panel(6, 6, 598, 318, PA, '(a) One episode',
      'AI2-THOR seed 8, cancel-early variant. Nobody asks; the agent meets the cue on its own route.')
FW, FH = 128, 96
xs = [20, 162, 304, 446]
y0 = 44
names = ['step0', 'step6', 'step11', 'step13']
caps = ['step 0  briefing', 'step 6  ON, out of view', 'step 11  cue in view', 'step 13  decision']
for x, n, cap in zip(xs, names, caps):
    A(f'<image x="{x}" y="{y0}" width="{FW}" height="{FH}" href="data:image/png;base64,{frame_b64(n)}" '
      f'preserveAspectRatio="none"/>')
    A(f'<rect x="{x}" y="{y0}" width="{FW}" height="{FH}" rx="3" fill="none" stroke="{BASE}" stroke-width="1"/>')
    A(f'<text x="{x}" y="{y0+FH+13}" class="b" font-weight="700">{cap}</text>')
# overlays
A(icon_robot(xs[0] + 15, y0 + 18, 0.85, INK))
A(bubble(xs[0] + 28, y0 + 6, 96, 40, ['Chores: Tomato →', 'Fridge, … If the', 'Toaster is ON,'], 'c'))
A(f'<text x="{xs[0]+37}" y="{y0+6+14+36}" class="c">turn it off.</text>')
A(f'<rect x="{xs[1]+74}" y="{y0+6}" width="50" height="28" rx="4" fill="#fff" stroke="{BASE}"/>')
A(icon_toaster(xs[1] + 89, y0 + 20, 0.65, OR))
A(icon_eye_off(xs[1] + 112, y0 + 20, 0.65, INK))
A(f'<rect x="{xs[2]+6}" y="{y0+6}" width="114" height="16" rx="3" fill="#fff" fill-opacity="0.94"/>')
A(icon_eye(xs[2] + 16, y0 + 14, 0.55, INK))
A(f'<text x="{xs[2]+26}" y="{y0+18}" class="c"><tspan class="red" font-weight="700">Toaster (ON)</tspan> in view</text>')
A(f'<rect x="{xs[3]+4}" y="{y0+6}" width="122" height="42" rx="4" fill="#fff" fill-opacity="0.95"/>')
A(f'<text x="{xs[3]+8}" y="{y0+20}" class="c"><tspan class="red" font-weight="700">toggle_off Toaster</tspan></text>')
A(f'<text x="{xs[3]+8}" y="{y0+31}" class="c red">   → commission error (EAC)</text>')
A(f'<text x="{xs[3]+8}" y="{y0+43}" class="c"><tspan class="blue" font-weight="700">goto Lettuce</tspan> → no error</text>')
# timeline
ty = y0 + FH + 34
A(f'<line x1="26" y1="{ty}" x2="{xs[3]+FW}" y2="{ty}" stroke="{MUTED}" stroke-width="2" marker-end="url(#arrg)"/>')
for x, col in [(xs[0] + 8, BL), (xs[1] + 64, OR), (xs[2] + 64, INK), (xs[3] + 64, RED)]:
    A(f'<circle cx="{x}" cy="{ty}" r="4.5" fill="{col}" stroke="#fff" stroke-width="1.5"/>')
A(icon_x(86, ty, 1.0, INK))
A(f'<text x="86" y="{ty-9}" class="m" font-size="8.5" text-anchor="middle">step 3</text>')
A(f'<text x="{xs[1]+64}" y="{ty-9}" class="m" font-size="8.5" text-anchor="middle">e = 6</text>')
A(icon_person(50, ty + 26, 0.85, MUTED))
A(bubble(62, ty + 8, 112, 30, ['“About the toaster,', 'never mind.”'], 'c'))
A(f'<text x="200" y="{ty+22}" class="m">one cancel message, never repeated; the trigger switches on while the agent is elsewhere</text>')
# four matched variants
vy = ty + 58
A(f'<text x="20" y="{vy}" class="h">Four matched variants per seed</text>')
A(f'<text x="196" y="{vy}" class="m">same scene, chores, trigger and event step; only the messages differ</text>')
rows = [('control', False, None, 'no instruction', 'floor'), ('live', True, None, 'never cancelled', 'EXEC'),
        ('cancel-early', True, 152, 'cancelled at e−3', 'EAC'), ('cancel-late', True, 214, 'cancelled at e+2', 'EAC')]
for i, (name, instr, cx, desc, met) in enumerate(rows):
    y = vy + 16 + i * 17
    A(f'<line x1="100" y1="{y}" x2="262" y2="{y}" stroke="{BASE}" stroke-width="1.6"/>')
    A(f'<text x="92" y="{y+3}" class="b" text-anchor="end">{name}</text>')
    A(f'<circle cx="110" cy="{y}" r="4" fill="{BL if instr else "#fff"}" stroke="{BL}" stroke-width="1.5"/>')
    A(f'<rect x="178" y="{y-4}" width="8" height="8" transform="rotate(45 182 {y})" fill="{OR}"/>')
    if cx:
        A(icon_x(cx, y, 0.8, INK))
    A(f'<text x="276" y="{y+3}" class="m">{desc} → <tspan class="h" font-size="9.5">{met}</tspan></text>')
ly = vy + 16 + 4 * 17 + 2
A(f'<g class="m" font-size="8.5"><text x="110" y="{ly}" text-anchor="middle">briefing</text>'
  f'<text x="182" y="{ly}" text-anchor="middle">trigger ON</text><text x="240" y="{ly}" text-anchor="middle">✕ cancel</text></g>')

# ============ (b) one step ============
panel(612, 6, 190, 318, PB, '(b) One step', 'actor fixed; memory varies')
bx, bw = 620, 172
A(icon_house(bx + 14, 56, 0.9, MUTED))
A(f'<text x="{bx+32}" y="53" class="h">World</text>')
A(f'<text x="{bx+32}" y="65" class="m">AI2-THOR · Habitat</text>')
A(f'<line x1="{bx+14}" y1="70" x2="{bx+14}" y2="86" stroke="{INK}" stroke-width="1.2" marker-end="url(#arr)"/>')
A(f'<text x="{bx+20}" y="82" class="m">observe()</text>')
A(bubble(bx, 90, bw, 30, ['You see: …, Mug, SinkBasin,', 'Toaster (ON), Window.'], 'c'))
A(f'<line x1="{bx+14}" y1="128" x2="{bx+14}" y2="142" stroke="{INK}" stroke-width="1.2" marker-end="url(#arr)"/>')
A(f'<rect x="{bx}" y="144" width="{bw}" height="80" rx="6" fill="#fff" stroke="{INK}" stroke-width="1.5"/>')
A(icon_note(bx + 16, 164, 0.95, INK))
A(f'<text x="{bx+32}" y="159" class="h">Memory design</text>')
A(f'<text x="{bx+32}" y="171" class="m">the independent variable</text>')
A(f'<rect x="{bx+6}" y="180" width="{bw-12}" height="17" rx="3" fill="{OR}" fill-opacity="0.14"/>')
A(f'<text x="{bx+10}" y="192" class="c" style="font-size:8.3px"><tspan class="or" font-weight="700">raw</tspan>  …if ON, turn it off.</text>')
A(f'<rect x="{bx+6}" y="201" width="{bw-12}" height="17" rx="3" fill="{BL}" fill-opacity="0.14"/>')
A(f'<text x="{bx+10}" y="213" class="c" style="font-size:8.3px"><tspan class="blue" font-weight="700">status</tspan>  CANCELLED, do NOT touch</text>')
A(f'<line x1="{bx+14}" y1="224" x2="{bx+14}" y2="238" stroke="{INK}" stroke-width="1.2" marker-end="url(#arr)"/>')
A(f'<text x="{bx+20}" y="234" class="m">+ last 6 steps</text>')
A(icon_robot(bx + 14, 256, 1.0, INK))
A(f'<text x="{bx+32}" y="253" class="h">LLM actor</text>')
A(f'<text x="{bx+32}" y="265" class="m">one model, fixed</text>')
A(f'<line x1="{bx+14}" y1="272" x2="{bx+14}" y2="286" stroke="{INK}" stroke-width="1.2" marker-end="url(#arr)"/>')
A(bubble(bx, 288, bw, 30, ['{"action": "toggle_off",', ' "arg": "Toaster"}'], 'c'))
A(f'<path d="M{bx+bw},303 L{bx+bw+8},303 L{bx+bw+8},56 L{bx+bw-60},56" fill="none" stroke="{INK}" '
  f'stroke-width="1.2" marker-end="url(#arr)"/>')

# ============ (c) grading ============
panel(810, 6, 184, 318, PC, '(c) Grading', 'from world state, not from replies')
gx = 822
A(f'<text x="{gx}" y="52" class="m">toaster state, cancel-early variant</text>')
A(f'<line x1="{gx+14}" y1="100" x2="{gx+166}" y2="100" stroke="{BASE}"/>')
A(f'<path d="M{gx+14},96 L{gx+52},96 L{gx+52},66 L{gx+124},66 L{gx+124},96 L{gx+166},96" fill="none" '
  f'stroke="{OR}" stroke-width="2.2"/>')
A(icon_x(gx + 30, 100, 0.9, INK))
A(f'<circle cx="{gx+124}" cy="96" r="4" fill="{RED}" stroke="#fff" stroke-width="1.2"/>')
A(f'<g class="m" font-size="8.5"><text x="{gx+10}" y="69" text-anchor="end">ON</text>'
  f'<text x="{gx+10}" y="100" text-anchor="end">off</text>'
  f'<text x="{gx+30}" y="114" text-anchor="middle">cancel, 3</text>'
  f'<text x="{gx+124}" y="114" text-anchor="middle">toggle, 13</text>'
  f'<text x="{gx+52}" y="62" text-anchor="middle">e = 6</text></g>')
A(f'<g transform="translate({gx+152},132) rotate(-12)"><rect x="-19" y="-9" width="38" height="18" rx="3" '
  f'fill="#fff" stroke="{RED}" stroke-width="1.8"/><text x="0" y="3.5" text-anchor="middle" font-size="10" '
  f'font-weight="700" fill="{RED}">EAC</text></g>')
A(f'<text x="{gx}" y="132" class="b">exec step 13 &gt; cancel step 3:</text>')
A(f'<text x="{gx}" y="145" class="b red" font-weight="700">executed after cancellation</text>')
ms = [(icon_x(0, 0, 0.8, RED), 'EAC', 'acted after the cancel', RED),
      ('<path d="M-5,0 l3,3 l7,-7" fill="none" stroke="%s" stroke-width="2.4"/>' % GR, 'EXEC', 'live variant: carried it out', INK),
      (icon_eye(0, 0, 0.55, INK), 'NOTICE', 'cue was ever in view', INK),
      ('<line x1="-6" y1="0" x2="6" y2="0" stroke="%s" stroke-width="3"/>' % INK, 'floor', 'control: no instruction', INK)]
for i, (ic, k, v, col) in enumerate(ms):
    y = 172 + i * 20
    A(f'<g transform="translate({gx+8},{y})">{ic}</g>')
    A(f'<text x="{gx+20}" y="{y+4}" class="h" fill="{col}">{k}</text>'
      f'<text x="{gx+20+(44 if k != "NOTICE" else 54)}" y="{y+4}" class="b" font-size="9">{v}</text>')
A(f'<rect x="{gx-2}" y="258" width="166" height="58" rx="6" fill="#fff" fill-opacity="0.8"/>')
A(f'<text x="{gx+6}" y="274" class="h">No judge, no self-report</text>')
A(f'<text x="{gx+6}" y="288" class="b" font-size="9">Outcomes are read from the</text>')
A(f'<text x="{gx+6}" y="300" class="b" font-size="9">simulator\'s event log; a reply-</text>')
A(f'<text x="{gx+6}" y="312" class="b" font-size="9">based grader misses about half.</text>')
A('</svg>')

svg_text = '\n'.join(svg)
open(f'{OUT}/fig_overview.svg', 'w').write(svg_text)
html = (f'<!doctype html><html><head><meta charset="utf-8"><style>@page{{size:{W}px {H}px;margin:0}}'
        f'html,body{{margin:0;padding:0}}svg{{display:block}}</style></head><body>{svg_text}</body></html>')
hp = os.path.join(OUT, 'overview_tmp.html')
open(hp, 'w').write(html)
CH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
subprocess.run([CH, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                f'--print-to-pdf={OUT}/fig_overview.pdf', 'file://' + hp], capture_output=True)
subprocess.run([CH, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--screenshot={OUT}/fig_overview.png',
                f'--window-size={W},{H}', '--force-device-scale-factor=2', 'file://' + hp], capture_output=True)
os.remove(hp)
print('written', f'{OUT}/fig_overview.svg / .pdf / .png')
