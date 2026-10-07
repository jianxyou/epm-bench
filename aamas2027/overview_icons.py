"""Flat SVG icons and the speech bubble used by the overview figure (split out of make_overview.py)."""
INK, MUTED, GRID, BASE = '#0b0b0b', '#6f6e68', '#dddcd5', '#c3c2b7'
OR, BL, RED, GR = '#eb6834', '#2a78d6', '#d03b3b', '#1baf7a'

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

