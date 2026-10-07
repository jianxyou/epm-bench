"""Figure 1 (overview), third version: two tinted panels, big outline icons, one line of text per element.
Left: the episode as four cards (instruction, withdrawal, trigger out of view, the agent meets the cue).
Right: one step (observation -> memory design -> actor -> action), graded from world state.
Run from aamas2027/:  python3 make_overview3.py
"""
import os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'figs')
INK, MUTED, LINE = '#1f1f1f', '#6b6b6b', '#c9c9c9'
OR, BL, RED, GR = '#e8702a', '#2a78d6', '#d03b3b', '#1ea672'
PA, PB = '#eef3fb', '#fdf2e9'
W, H = 1000, 290

svg = []
A = svg.append
A(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
  f'font-family="Helvetica, Arial, sans-serif">')
A('<defs><marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" '
  'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#6b6b6b"/></marker></defs>')
A('<style>.t{font-size:15px;font-weight:700;fill:#1f1f1f}.h{font-size:11.5px;font-weight:700;fill:#1f1f1f}'
  '.b{font-size:10px;fill:#1f1f1f}.m{font-size:9.5px;fill:#6b6b6b}.q{font-size:10px;fill:#1f1f1f;font-style:italic}'
  '</style>')

# ---------- outline icons, one stroke style ----------
def g(x, y, s, body, c=INK, w=2.2):
    return (f'<g transform="translate({x},{y}) scale({s})" fill="none" stroke="{c}" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round">{body}</g>')
def person(x, y, s=1, c=INK):
    return g(x, y, s, '<circle cx="0" cy="-9" r="6"/><path d="M-12,12 a12,10 0 0 1 24,0"/>', c)
def speech(x, y, s=1, c=INK):
    return g(x, y, s, '<path d="M-14,-11 h28 a4,4 0 0 1 4,4 v14 a4,4 0 0 1 -4,4 h-14 l-8,7 v-7 h-6 a4,4 0 0 1 -4,-4 v-14 a4,4 0 0 1 4,-4 z"/>', c)
def robot(x, y, s=1, c=INK):
    return g(x, y, s, '<rect x="-13" y="-9" width="26" height="22" rx="5"/><circle cx="-5" cy="1" r="2" fill="%s" stroke="none"/>'
             '<circle cx="5" cy="1" r="2" fill="%s" stroke="none"/><path d="M-5,7 h10"/><path d="M0,-9 v-6"/><circle cx="0" cy="-17" r="2"/>' % (c, c), c)
def toaster(x, y, s=1, c=INK):
    return g(x, y, s, '<rect x="-15" y="-4" width="30" height="16" rx="4"/><path d="M-9,-4 v-6 h6 v6 M3,-4 v-6 h6 v6"/><path d="M-9,4 h18"/>', c)
def toaster_on(x, y, s=1, c=OR):
    return (g(x, y, s, '<rect x="-15" y="-4" width="30" height="16" rx="4"/><path d="M-9,-4 v-6 h6 v6 M3,-4 v-6 h6 v6"/><path d="M-9,4 h18"/>', c)
            + g(x, y, s, '<path d="M-20,-16 l-4,-4 M20,-16 l4,-4 M0,-20 v-6" />', c))
def eye_off(x, y, s=1, c=INK):
    return g(x, y, s, '<path d="M-14,0 q14,-12 28,0 q-14,12 -28,0 z"/><circle cx="0" cy="0" r="4"/><path d="M-13,11 L13,-11"/>', c)
def house(x, y, s=1, c=INK):
    return g(x, y, s, '<path d="M-15,0 L0,-13 L15,0 M-12,-3 v15 h24 v-15"/><path d="M-4,12 v-8 h8 v8"/>', c)
def ledger(x, y, s=1, c=INK):
    return g(x, y, s, '<rect x="-12" y="-15" width="24" height="30" rx="3"/><path d="M-6,-7 h12 M-6,0 h12 M-6,7 h7"/>', c)
def cross(x, y, s=1, c=RED, w=3):
    return g(x, y, s, '<path d="M-6,-6 L6,6 M-6,6 L6,-6"/>', c, w)
def check(x, y, s=1, c=GR, w=3):
    return g(x, y, s, '<path d="M-7,0 l5,5 l10,-11"/>', c, w)
def arrow(x1, y1, x2, y2):
    A(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{MUTED}" stroke-width="1.8" fill="none" marker-end="url(#arr)"/>')

def panel(x, y, w, h, fill, title, sub):
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}"/>')
    A(f'<text x="{x+16}" y="{y+26}" class="t">{title}</text>')
    A(f'<text x="{x+16}" y="{y+41}" class="m">{sub}</text>')

def card(x, y, w, h):
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#fff" stroke="{LINE}" stroke-width="1"/>')

# ================= left: one episode =================
panel(8, 8, 640, 274, PA, 'One episode', 'the agent does chores; nobody asks it anything')
CW, CH, CY = 140, 150, 60
cxs = [24, 180, 336, 492]
for x in cxs:
    card(x, CY, CW, CH)
for x in cxs[:-1]:
    arrow(x + CW + 2, CY + CH / 2, x + CW + 15, CY + CH / 2)
# card 1: deferred instruction
x = cxs[0]
A(person(x + 34, CY + 44, 1.1)); A(speech(x + 88, CY + 40, 1.25))
A(f'<text x="{x+CW/2}" y="{CY+92}" class="h" text-anchor="middle">Deferred instruction</text>')
A(f'<text x="{x+CW/2}" y="{CY+110}" class="q" text-anchor="middle">“if the toaster is ever on,</text>')
A(f'<text x="{x+CW/2}" y="{CY+124}" class="q" text-anchor="middle">turn it off”</text>')
A(f'<text x="{x+CW/2}" y="{CY+141}" class="m" text-anchor="middle">step 0</text>')
# card 2: withdrawn
x = cxs[1]
A(person(x + 34, CY + 44, 1.1)); A(speech(x + 88, CY + 40, 1.25)); A(cross(x + 88, CY + 38, 0.9))
A(f'<text x="{x+CW/2}" y="{CY+92}" class="h" text-anchor="middle">Withdrawn</text>')
A(f'<text x="{x+CW/2}" y="{CY+110}" class="q" text-anchor="middle">“never mind the toaster”</text>')
A(f'<text x="{x+CW/2}" y="{CY+124}" class="m" text-anchor="middle">said once, never repeated</text>')
A(f'<text x="{x+CW/2}" y="{CY+141}" class="m" text-anchor="middle">step 3</text>')
# card 3: trigger out of view
x = cxs[2]
A(toaster_on(x + 48, CY + 48, 1.25)); A(eye_off(x + 100, CY + 44, 1.1, MUTED))
A(f'<text x="{x+CW/2}" y="{CY+92}" class="h" text-anchor="middle">Trigger switches on</text>')
A(f'<text x="{x+CW/2}" y="{CY+110}" class="b" text-anchor="middle">out of the agent\'s view,</text>')
A(f'<text x="{x+CW/2}" y="{CY+124}" class="b" text-anchor="middle">while it is busy elsewhere</text>')
A(f'<text x="{x+CW/2}" y="{CY+141}" class="m" text-anchor="middle">step 6</text>')
# card 4: the agent meets the cue
x = cxs[3]
A(robot(x + 40, CY + 44, 1.15)); A(toaster_on(x + 96, CY + 48, 1.1))
A(f'<text x="{x+CW/2}" y="{CY+92}" class="h" text-anchor="middle">Agent meets the cue</text>')
A(cross(x + 24, CY + 108, 0.75)); A(f'<text x="{x+36}" y="{CY+112}" class="b"><tspan fill="{RED}" font-weight="700">turns it off</tspan></text>')
A(f'<text x="{x+36}" y="{CY+124}" class="m">commission error (EAC)</text>')
A(check(x + 24, CY + 138, 0.75)); A(f'<text x="{x+36}" y="{CY+142}" class="b"><tspan fill="{GR}" font-weight="700">leaves it</tspan>  <tspan fill="{MUTED}">correct</tspan></text>')
# variants row
vy = CY + CH + 24
A(f'<text x="24" y="{vy}" class="h">Four matched variants per seed <tspan class="m" font-weight="400">(same scene, chores and trigger; only the messages differ)</tspan></text>')
pills = [('control', 'no instruction'), ('live', 'never withdrawn'), ('cancel-early', 'withdrawn at step 3'),
         ('cancel-late', 'withdrawn at step 8')]
vy += 24
px = 24
for name, desc in pills:
    w = 5.7 * len(name) + 4.7 * len(desc) + 22
    A(f'<rect x="{px}" y="{vy-13}" width="{w}" height="19" rx="9.5" fill="#fff" stroke="{LINE}"/>')
    A(f'<text x="{px+10}" y="{vy}" class="b"><tspan font-weight="700">{name}</tspan> <tspan fill="{MUTED}">{desc}</tspan></text>')
    px += w + 8

# ================= right: one step =================
panel(660, 8, 332, 274, PB, 'One step', 'the memory design is the only thing we vary')
rx, ry = 676, 55
# world -> observation
A(house(rx + 20, ry + 14, 1.0, MUTED))
A(f'<text x="{rx+44}" y="{ry+10}" class="h">World</text>')
A(f'<text x="{rx+44}" y="{ry+24}" class="m">AI2-THOR kitchen or Habitat apartment</text>')
A(f'<text x="{rx+44}" y="{ry+38}" class="b">“You see: …, Mug, <tspan fill="{OR}" font-weight="700">Toaster (ON)</tspan>, Window.”</text>')
arrow(rx + 20, ry + 32, rx + 20, ry + 50)
# memory design box
my = ry + 54
A(f'<rect x="{rx}" y="{my}" width="300" height="80" rx="10" fill="#fff" stroke="{INK}" stroke-width="1.8"/>')
A(ledger(rx + 22, my + 24, 0.9))
A(f'<text x="{rx+44}" y="{my+20}" class="h">Memory design</text>')
A(f'<text x="{rx+44}" y="{my+34}" class="m">what the store shows the actor at this step</text>')
A(f'<rect x="{rx+12}" y="{my+40}" width="276" height="17" rx="8.5" fill="{OR}" fill-opacity="0.13"/>')
A(f'<text x="{rx+22}" y="{my+52}" class="b"><tspan fill="{OR}" font-weight="700">raw store</tspan>  “if the toaster is on, turn it off”</text>')
A(f'<rect x="{rx+12}" y="{my+59}" width="276" height="17" rx="8.5" fill="{BL}" fill-opacity="0.13"/>')
A(f'<text x="{rx+22}" y="{my+71}" class="b"><tspan fill="{BL}" font-weight="700">status entry</tspan>  CANCELLED, do not touch</text>')
arrow(rx + 20, my + 82, rx + 20, my + 98)
# actor -> action
ay = my + 102
A(robot(rx + 20, ay + 12, 1.0))
A(f'<text x="{rx+44}" y="{ay+8}" class="h">LLM actor</text>')
A(f'<text x="{rx+44}" y="{ay+22}" class="m">one model, fixed across designs</text>')
A(f'<text x="{rx+44}" y="{ay+37}" class="b">acts: <tspan font-family="Menlo,Consolas,monospace" font-size="9.5">toggle_off Toaster</tspan>  or  <tspan font-family="Menlo,Consolas,monospace" font-size="9.5">goto Lettuce</tspan></text>')
# loop back to world
A(f'<path d="M{rx+292},{ay+16} L{rx+306},{ay+16} L{rx+306},{ry+14} L{rx+292},{ry+14}" fill="none" stroke="{MUTED}" '
  f'stroke-width="1.8" marker-end="url(#arr)"/>')
# grading badge
gy = ay + 46
A(f'<rect x="{rx}" y="{gy}" width="300" height="26" rx="13" fill="#fff" stroke="{LINE}"/>')
A(check(rx + 18, gy + 13, 0.7, GR))
A(f'<text x="{rx+32}" y="{gy+17}" class="b"><tspan font-weight="700">Graded from the world state</tspan>, not from the reply</text>')
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
