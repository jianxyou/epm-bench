"""Figure 1 (overview) as SVG -> PDF. Pictorial: real first-person frames + flat icons, little text.
Run from embodied_pm/:  python3 aamas2027/make_overview.py
"""
import base64, io, json, os, subprocess
import numpy as np
from PIL import Image, ImageDraw

TH = '/private/tmp/claude-501/-Users-jianxin-Desktop-my-project/281fe8db-511d-41cc-9e57-a0a441fc7a20/scratchpad/thor_story'
OUT = 'aamas2027/figs'
INK, MUTED, GRID, BASE = '#0b0b0b', '#898781', '#e1e0d9', '#c3c2b7'
OR, BL, RED, GR = '#eb6834', '#2a78d6', '#d03b3b', '#1baf7a'

def frame_b64(pol, t, box=None, label=None, dim=False):
    im = Image.fromarray(np.load(f'{TH}/{pol}_t{t}.npy')).resize((320, 240), Image.LANCZOS)
    if dim:
        im = Image.blend(im, Image.new('RGB', im.size, (255, 255, 255)), 0.35)
    if box:
        d = ImageDraw.Draw(im); x0, y0, x1, y1 = [v * 0.5 for v in box]
        d.rectangle([x0 - 2, y0 - 2, min(x1 + 2, 318), y1 + 2], outline=(208, 59, 59), width=4)
    buf = io.BytesIO(); im.save(buf, format='PNG', optimize=True)
    return base64.b64encode(buf.getvalue()).decode()

tb = json.load(open(f'{TH}/bank_toaster.json'))
bbox11 = list(tb['11']['bbox'].values())[0]

# ---------------- icons (flat, single colour) ----------------
def icon_person(x, y, s=1.0, c=MUTED):
    return f'<g transform="translate({x},{y}) scale({s})"><circle cx="0" cy="-6" r="5.2" fill="{c}"/><path d="M-9,8 a9,7 0 0 1 18,0 z" fill="{c}"/></g>'
def icon_robot(x, y, s=1.0, c=INK):
    return (f'<g transform="translate({x},{y}) scale({s})"><rect x="-10" y="-8" width="20" height="16" rx="4" fill="{c}"/>'
            f'<circle cx="-4" cy="-1" r="2.2" fill="#fff"/><circle cx="4" cy="-1" r="2.2" fill="#fff"/>'
            f'<rect x="-4" y="3.5" width="8" height="1.8" rx="0.9" fill="#fff"/><line x1="0" y1="-8" x2="0" y2="-13" stroke="{c}" stroke-width="2"/><circle cx="0" cy="-14" r="2" fill="{c}"/></g>')
def icon_toaster(x, y, s=1.0, c=OR):
    return (f'<g transform="translate({x},{y}) scale({s})"><rect x="-13" y="-4" width="26" height="15" rx="3" fill="{c}"/>'
            f'<rect x="-8" y="-8" width="6" height="6" fill="{c}"/><rect x="2" y="-8" width="6" height="6" fill="{c}"/><rect x="-9" y="1" width="18" height="2" fill="#fff"/></g>')
def icon_eye_off(x, y, s=1.0, c=INK):
    return (f'<g transform="translate({x},{y}) scale({s})" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round">'
            f'<path d="M-11,0 Q0,-9 11,0 Q0,9 -11,0 z"/><circle cx="0" cy="0" r="3.2" fill="{c}" stroke="none"/><line x1="-11" y1="9" x2="11" y2="-9"/></g>')
def icon_eye(x, y, s=1.0, c=INK):
    return (f'<g transform="translate({x},{y}) scale({s})" fill="none" stroke="{c}" stroke-width="2">'
            f'<path d="M-11,0 Q0,-9 11,0 Q0,9 -11,0 z"/><circle cx="0" cy="0" r="3.2" fill="{c}" stroke="none"/></g>')
def icon_house(x, y, s=1.0, c=MUTED):
    return (f'<g transform="translate({x},{y}) scale({s})"><path d="M-14,0 L0,-12 L14,0 L14,12 L-14,12 z" fill="{c}"/>'
            f'<rect x="-4" y="3" width="8" height="9" fill="#fff"/></g>')
def icon_note(x, y, s=1.0, c=INK):
    return (f'<g transform="translate({x},{y}) scale({s})"><rect x="-11" y="-13" width="22" height="26" rx="2" fill="#fff" stroke="{c}" stroke-width="1.6"/>'
            f'<line x1="-6" y1="-6" x2="6" y2="-6" stroke="{c}" stroke-width="1.6"/><line x1="-6" y1="0" x2="6" y2="0" stroke="{c}" stroke-width="1.6"/><line x1="-6" y1="6" x2="2" y2="6" stroke="{c}" stroke-width="1.6"/></g>')
def icon_x(x, y, s=1.0, c=INK):
    return f'<g transform="translate({x},{y}) scale({s})"><line x1="-4.5" y1="-4.5" x2="4.5" y2="4.5" stroke="{c}" stroke-width="2.8"/><line x1="-4.5" y1="4.5" x2="4.5" y2="-4.5" stroke="{c}" stroke-width="2.8"/></g>'
def bubble(x, y, w, h, lines, cls='c', tail='left', fill='#fff', stroke=BASE):
    tx = x + 12 if tail == 'left' else x + w - 12
    path = (f'<path d="M{x+6},{y} h{w-12} a6,6 0 0 1 6,6 v{h-12} a6,6 0 0 1 -6,6 h{-(w-12)} a6,6 0 0 1 -6,-6 v{-(h-12)} a6,6 0 0 1 6,-6 z" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
            f'<path d="M{tx-5},{y+h} l5,7 l5,-7 z" fill="{fill}" stroke="{stroke}" stroke-width="1"/><line x1="{tx-4.5}" y1="{y+h}" x2="{tx+4.5}" y2="{y+h}" stroke="{fill}" stroke-width="2"/>')
    txt = ''.join(f'<text x="{x+9}" y="{y+14+i*12}" class="{cls}">{l}</text>' for i, l in enumerate(lines))
    return path + txt

svg = []
A = svg.append
A('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 350" width="1000" height="350" font-family="Helvetica, Arial, sans-serif">')
A('''<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#0b0b0b"/></marker>
<marker id="arrg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#898781"/></marker></defs>
<style>.t{font-size:15px;font-weight:700;fill:#0b0b0b}.h{font-size:11px;font-weight:700;fill:#0b0b0b}.b{font-size:10px;fill:#0b0b0b}.m{font-size:9.4px;fill:#898781}
.c{font-size:9.2px;fill:#0b0b0b;font-family:Menlo,Consolas,monospace}.red{fill:#d03b3b}.blue{fill:#2a78d6}.or{fill:#eb6834}</style>''')

# ============ (a) frames strip ============
A('<text x="14" y="22" class="t">(a) An episode</text>')
A('<text x="126" y="22" class="m">as the agent sees it — AI2-THOR seed 8, cancel-early twin</text>')
FW, FH = 126, 94
xs = [14, 154, 294, 434]
steps = [(0, 'bank', None, False), (6, 'bank', None, True), (11, 'bank', bbox11, False), (13, 'bank', bbox11, False)]
caps = ['step 0', 'step 6', 'step 11', 'step 13']
for (t, pol, box, dim), x, cap in zip(steps, xs, caps):
    A(f'<image x="{x}" y="34" width="{FW}" height="{FH}" href="data:image/png;base64,{frame_b64(pol, t, box, dim=dim)}" preserveAspectRatio="none"/>')
    A(f'<rect x="{x}" y="34" width="{FW}" height="{FH}" fill="none" stroke="{BASE}" stroke-width="1"/>')
    A(f'<text x="{x}" y="139" class="m">{cap}</text>')
# overlays on frames
# step 0: robot + clipboard bubble
A(icon_robot(xs[0] + 16, 52, 0.9, INK))
A(bubble(xs[0] + 30, 40, 92, 40, ['Chores: Tomato →', 'Fridge, … If the', 'Toaster is ON,'], 'c'))
A(f'<text x="{xs[0]+39}" y="{40+14+36}" class="c">turn it off.</text>')
# step 6: toaster ON out of view
A(f'<rect x="{xs[1]+70}" y="40" width="52" height="30" rx="4" fill="#fff" stroke="{BASE}"/>')
A(icon_toaster(xs[1] + 86, 55, 0.7, OR)); A(icon_eye_off(xs[1] + 110, 55, 0.7, INK))
A(f'<rect x="{xs[1]+4}" y="{34+FH-20}" width="118" height="15" rx="3" fill="#fff" fill-opacity="0.92"/>')
A(f'<text x="{xs[1]+8}" y="{34+FH-9}" class="b" font-weight="700">Toaster switched ON, <tspan class="or">out of view</tspan></text>')
# step 11: eye + observation
A(icon_eye(xs[2] + 14, 46, 0.7, INK))
A(f'<rect x="{xs[2]+24}" y="38" width="98" height="16" rx="3" fill="#fff" fill-opacity="0.92"/>')
A(f'<text x="{xs[2]+28}" y="50" class="c"><tspan class="red" font-weight="700">Toaster (ON)</tspan> in view</text>')
# step 13: the fork
A(f'<rect x="{xs[3]+6}" y="38" width="114" height="46" rx="4" fill="#fff" fill-opacity="0.94"/>')
A(f'<text x="{xs[3]+10}" y="50" class="c"><tspan class="red" font-weight="700">toggle_off Toaster</tspan></text>')
A(f'<text x="{xs[3]+10}" y="62" class="c"><tspan class="red">  → commission error</tspan></text>')
A(f'<text x="{xs[3]+10}" y="76" class="c"><tspan class="blue" font-weight="700">goto Lettuce</tspan> → no error</text>')
# user bubble between step 0 and step 6 (step 3)
A(f'<line x1="{xs[0]+FW}" y1="150" x2="{xs[3]+FW}" y2="150" stroke="{BASE}" stroke-width="2" marker-end="url(#arrg)"/>')
A(f'<line x1="30" y1="150" x2="{xs[0]+FW}" y2="150" stroke="{BASE}" stroke-width="2"/>')
for x, col in [(xs[0] + 8, BL), (xs[1] + 63, OR), (xs[2] + 63, INK), (xs[3] + 63, RED)]:
    A(f'<circle cx="{x}" cy="150" r="4.5" fill="{col}" stroke="#fff" stroke-width="1.5"/>')
A(icon_x(84, 150, 1.0, INK))
A(icon_person(52, 176, 0.9, MUTED))
A(bubble(64, 158, 110, 30, ['“About the toaster,', 'never mind.”'], 'c'))
A('<text x="84" y="141" class="m" font-size="8.5" text-anchor="middle">step 3</text>')
A(f'<text x="{xs[1]+63}" y="166" class="m" font-size="8.5" text-anchor="middle">e = 6</text>')
A('<text x="200" y="180" class="m">nobody asks; the cue appears among everything else in the room,</text>')
A('<text x="200" y="192" class="m">and the agent acts, or not, on its own</text>')

# four twins (compact)
A('<text x="14" y="214" class="h">Four matched variants per seed</text>')
A('<text x="128" y="214" class="m">same scene, chores, trigger, event step; only the messages differ</text>')
rows = [('control', False, None, 'no instruction → floor'), ('live', True, None, 'never cancelled → EXEC'),
        ('cancel-early', True, 148, 'cancelled at e−3 → EAC'), ('cancel-late', True, 212, 'cancelled at e+2 → EAC')]
for i, (name, instr, cx, desc) in enumerate(rows):
    y = 232 + i * 19
    A(f'<line x1="96" y1="{y}" x2="262" y2="{y}" stroke="{GRID}" stroke-width="1.6"/>')
    A(f'<text x="88" y="{y+3}" class="b" text-anchor="end">{name}</text>')
    A(f'<circle cx="106" cy="{y}" r="4" fill="{BL if instr else "#fff"}" stroke="{BL}" stroke-width="1.5"/>')
    A(f'<rect x="176" y="{y-4}" width="8" height="8" transform="rotate(45 180 {y})" fill="{OR}"/>')
    if cx: A(icon_x(cx, y, 0.8, INK))
    A(f'<text x="274" y="{y+3}" class="m">{desc}</text>')
A('<g class="m" font-size="8.5"><text x="106" y="316" text-anchor="middle">briefing</text><text x="180" y="316" text-anchor="middle">trigger ON</text><text x="240" y="316" text-anchor="middle">✕ cancel</text></g>')

# divider
A(f'<line x1="576" y1="14" x2="576" y2="340" stroke="{GRID}"/>')

# ============ (b) one step as a loop ============
A('<text x="590" y="22" class="t">(b) One step</text>')
A('<text x="686" y="22" class="m">actor fixed; memory varies</text>')
cx0 = 690
# world
A(icon_house(cx0 - 60, 52, 1.0, MUTED)); A(f'<text x="{cx0-40}" y="48" class="h">World</text>'); A(f'<text x="{cx0-40}" y="61" class="m">AI2-THOR · Habitat</text>')
A(f'<line x1="{cx0-60}" y1="66" x2="{cx0-60}" y2="84" stroke="{INK}" stroke-width="1.2" marker-end="url(#arr)"/>')
A(f'<text x="{cx0-52}" y="80" class="m">observe()</text>')
# observation bubble
A(bubble(cx0 - 80, 88, 170, 30, ['You see: …, Mug, SinkBasin,', 'Toaster (ON), Window.'], 'c', tail='left'))
A(f'<line x1="{cx0-60}" y1="126" x2="{cx0-60}" y2="140" stroke="{INK}" stroke-width="1.2" marker-end="url(#arr)"/>')
# memory: notebook with two stickies
A(f'<rect x="{cx0-80}" y="142" width="170" height="82" rx="6" fill="#fff" stroke="{INK}" stroke-width="1.6"/>')
A(icon_note(cx0 - 64, 162, 1.0, INK))
A(f'<text x="{cx0-46}" y="157" class="h">Memory design</text>'); A(f'<text x="{cx0-46}" y="169" class="m">the independent variable</text>')
A(f'<rect x="{cx0-74}" y="178" width="158" height="18" rx="3" fill="{OR}" fill-opacity="0.13"/>')
A(f'<text x="{cx0-70}" y="190" class="c"><tspan class="or" font-weight="700">raw</tspan>  …if ON, turn it off.</text>')
A(f'<rect x="{cx0-74}" y="200" width="158" height="18" rx="3" fill="{BL}" fill-opacity="0.13"/>')
A(f'<text x="{cx0-70}" y="212" class="c"><tspan class="blue" font-weight="700">status</tspan>  CANCELLED: do NOT touch.</text>')
A(f'<line x1="{cx0-60}" y1="224" x2="{cx0-60}" y2="238" stroke="{INK}" stroke-width="1.2" marker-end="url(#arr)"/>')
A(f'<text x="{cx0-52}" y="234" class="m">+ last 6 steps</text>')
# actor
A(icon_robot(cx0 - 60, 258, 1.1, INK)); A(f'<text x="{cx0-40}" y="254" class="h">LLM actor</text>'); A(f'<text x="{cx0-40}" y="267" class="m">one model, fixed</text>')
A(f'<line x1="{cx0-60}" y1="274" x2="{cx0-60}" y2="288" stroke="{INK}" stroke-width="1.2" marker-end="url(#arr)"/>')
A(bubble(cx0 - 80, 292, 170, 32, ['{"action": "toggle_off",', ' "arg": "Toaster"}'], 'c', tail='left'))
# loop back
A(f'<path d="M{cx0+91},308 L{cx0+106},308 L{cx0+106},52 L{cx0+40},52" fill="none" stroke="{INK}" stroke-width="1.2" marker-end="url(#arr)"/>')
A(f'<text x="{cx0+102}" y="178" class="m" transform="rotate(-90 {cx0+102} 178)" text-anchor="middle">act()</text>')
A(f'<text x="{cx0-80}" y="336" class="m">harness only: trigger ON at e, out of view;</text>')
A(f'<text x="{cx0-80}" y="347" class="m">one cancel message, never repeated</text>')

# divider
A(f'<line x1="808" y1="14" x2="808" y2="340" stroke="{GRID}"/>')

# ============ (c) grading ============
A('<text x="822" y="22" class="t">(c) Grading</text>')
A('<text x="906" y="22" class="m">from world state</text>')
A('<text x="822" y="42" class="m">toaster state, cancel-early twin</text>')
A(f'<line x1="836" y1="96" x2="990" y2="96" stroke="{BASE}"/>')
A(f'<path d="M836,92 L876,92 L876,62 L946,62 L946,92 L990,92" fill="none" stroke="{OR}" stroke-width="2.2"/>')
A(icon_x(852, 96, 0.9, INK)); A(f'<circle cx="946" cy="92" r="4" fill="{RED}" stroke="#fff" stroke-width="1.2"/>')
A('<g class="m" font-size="8.8"><text x="830" y="65" text-anchor="end">ON</text><text x="830" y="96" text-anchor="end">off</text>'
  '<text x="852" y="110" text-anchor="middle">cancel, 3</text><text x="946" y="110" text-anchor="middle">toggle, 13</text><text x="876" y="58" text-anchor="middle">e = 6</text></g>')
# EAC stamp
A(f'<g transform="translate(972,128) rotate(-12)"><rect x="-19" y="-9" width="38" height="18" rx="3" fill="#fff" stroke="{RED}" stroke-width="1.8"/><text x="0" y="3.5" text-anchor="middle" font-size="10" font-weight="700" fill="{RED}">EAC</text></g>')
A('<text x="822" y="130" class="b">exec step 13 &gt; cancel step 3</text>')
A('<text x="822" y="143" class="b red" font-weight="700">executed after cancellation</text>')
# metrics with icons
ms = [(icon_x(0, 0, 0.8, RED), 'EAC', 'acted after the cancel', RED),
      ('<path d="M-5,0 l3,3 l7,-7" fill="none" stroke="%s" stroke-width="2.4"/>' % GR, 'EXEC', 'live twin: carried it out', INK),
      (icon_eye(0, 0, 0.55, INK), 'NOTICE', 'cue was ever in view', INK),
      ('<line x1="-6" y1="0" x2="6" y2="0" stroke="%s" stroke-width="3"/>' % INK, 'floor', 'control: no instruction', INK)]
for i, (ic, k, v, col) in enumerate(ms):
    y = 168 + i * 20
    A(f'<g transform="translate(830,{y})">{ic}</g>')
    A(f'<text x="842" y="{y+4}" class="h" fill="{col}">{k}</text><text x="{842 + (44 if k!="NOTICE" else 52)}" y="{y+4}" class="b">{v}</text>')
A(f'<rect x="822" y="256" width="168" height="80" rx="6" fill="#f4f3ef"/>')
A('<text x="830" y="272" class="h">No judge, no self-report</text>')
A('<text x="830" y="287" class="b">Read from the simulator\'s event</text>')
A('<text x="830" y="299" class="b">log. Asking the agent at the end</text>')
A('<text x="830" y="311" class="b">of the episode passes 53% of</text>')
A('<text x="830" y="323" class="b">those that had already acted.</text>')
A('</svg>')

svg_text = '\n'.join(svg)
open(f'{OUT}/fig_overview.svg', 'w').write(svg_text)
html = '<!doctype html><html><head><meta charset="utf-8"><style>@page{size:1000px 350px;margin:0}html,body{margin:0;padding:0}svg{display:block}</style></head><body>' + svg_text + '</body></html>'
hp = '/private/tmp/claude-501/-Users-jianxin-Desktop-my-project/281fe8db-511d-41cc-9e57-a0a441fc7a20/scratchpad/overview.html'
open(hp, 'w').write(html)
CH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
subprocess.run([CH, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={os.path.abspath(OUT)}/fig_overview.pdf', 'file://' + hp], capture_output=True)
subprocess.run([CH, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--screenshot=/private/tmp/claude-501/-Users-jianxin-Desktop-my-project/281fe8db-511d-41cc-9e57-a0a441fc7a20/scratchpad/overview.png',
                '--window-size=1000,350', '--force-device-scale-factor=2', 'file://' + hp], capture_output=True)
print('written', f'{OUT}/fig_overview.svg/.pdf')
