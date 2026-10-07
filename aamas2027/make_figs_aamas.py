"""Figures for the AAMAS paper. Run from embodied_pm/:  python3 aamas2027/make_figs_aamas.py
Reads paper_v02/stats.json (run make_stats.py first), results CSVs and traces.
"""
import json, math, csv, glob, re, os, collections
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, FancyBboxPatch

OUT = 'aamas2027/figs'
S = json.load(open('paper_v02/stats.json'))
C = {'none': '#1baf7a', 'bank': '#eb6834', 'sched2': '#2a78d6', 'grey': '#b5b3ab', 'rwim': '#8e5bd6', 'sonnet': '#d6a15b'}
INK, MUTED, GRID, BASE = '#0b0b0b', '#898781', '#e1e0d9', '#c3c2b7'
plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 8, 'axes.edgecolor': BASE, 'axes.linewidth': 0.8,
                     'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.labelcolor': INK, 'text.color': INK,
                     'axes.spines.top': False, 'axes.spines.right': False, 'ytick.major.width': 0.6, 'xtick.major.size': 0})


def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * (c - h), 100 * (c + h))


def style(ax, ylabel, ymax=100):
    ax.yaxis.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True)
    ax.set_ylim(0, ymax); ax.set_yticks([0, 25, 50, 75, 100]); ax.set_ylabel(ylabel)
    ax.spines['left'].set_visible(False); ax.spines['bottom'].set_color(BASE)


def save(fig, name):
    fig.savefig(f'{OUT}/{name}.pdf', bbox_inches='tight'); fig.savefig(f'{OUT}/{name}.png', dpi=200, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------- Fig: episode timeline (four twins)
fig, ax = plt.subplots(figsize=(3.3, 1.75))
e = 6
rows = [('control', None, None), ('live', 0, None), ('cancel-early', 0, e - 3), ('cancel-late', 0, e + 2)]
for i, (name, instr, cancel) in enumerate(rows):
    y = len(rows) - 1 - i
    ax.plot([0, 40], [y, y], color=BASE, linewidth=1.2, zorder=1)
    ax.text(-1.2, y, name, ha='right', va='center', fontsize=7, color=INK)
    if instr is not None:
        ax.scatter([0], [y], s=34, color=C['sched2'], zorder=3, edgecolor='white', linewidth=0.8)
    else:
        ax.scatter([0], [y], s=34, facecolor='white', edgecolor=C['sched2'], zorder=3, linewidth=1.2)
    ax.scatter([e], [y], s=40, marker='D', color=C['bank'], zorder=3, edgecolor='white', linewidth=0.8)
    if cancel is not None:
        ax.scatter([cancel], [y], s=48, marker='X', color=INK, zorder=4)
    ax.axvspan(e + 0.5, 40, ymin=(y + 0.15) / len(rows), ymax=(y + 0.85) / len(rows), color='#f3e9e5', zorder=0)
ax.set_xlim(-0.5, 40); ax.set_ylim(-0.6, len(rows) - 0.4)
ax.set_yticks([]); ax.spines['left'].set_visible(False)
ax.set_xticks([0, e, 40]); ax.set_xticklabels(['0\nbriefing', 'e\ntrigger fires', '40'], fontsize=6.5)
ax.text(e - 3, 1.45, 'e−3', ha='center', va='bottom', fontsize=5.8, color=MUTED)
ax.text(e + 2, 0.45, 'e+2', ha='center', va='bottom', fontsize=5.8, color=MUTED)
ax.set_xlabel('step', fontsize=7, labelpad=1)
h = [Line2D([0], [0], marker='o', color='w', markerfacecolor=C['sched2'], markersize=6, label='instruction given'),
     Line2D([0], [0], marker='o', color='w', markerfacecolor='white', markeredgecolor=C['sched2'], markersize=6, label='no instruction'),
     Line2D([0], [0], marker='D', color='w', markerfacecolor=C['bank'], markersize=6, label='trigger switched on, out of view'),
     Line2D([0], [0], marker='X', color='w', markerfacecolor=INK, markersize=6, label='user cancels'),
     Patch(color='#f3e9e5', label='cue can be met; graded from world state')]
ax.legend(handles=h, loc='upper center', bbox_to_anchor=(0.5, -0.42), ncol=2, frameon=False, fontsize=5.8, handletextpad=0.3, columnspacing=0.8)
save(fig, 'fig_twins')

# ---------------------------------------------------------------- Fig: ablation (replaces the table)
m = S['main']['gpt4omini']; g = S['main']['gemini']
spec = [('bank', 'raw\nstore', C['bank']), ('retr', 'retrieval', C['grey']), ('summ', 'rolling\nsummary', C['grey']),
        ('sched1e', 'status\nannotated,\nimperative kept', C['grey']), ('retr2', 'status\nentry in\nretrieval', C['grey']),
        ('sched2', 'status-\ntracked', C['sched2']),
        ('rwim4', 'self-kept\nfree-form', C['rwim']), ('rwim5', 'self-kept\nfixed\nwording', C['rwim']),
        ('rwim5@claude-sonnet-', 'self-kept\nSonnet 5\nkeeps it', C['sonnet'])]
fig, (a, b) = plt.subplots(2, 1, figsize=(6.9, 2.75), sharex=True)
for ax, key_k, key_n, ylabel, title in [(a, 'eac_k', 'eac_n', 'EAC (%)', '(a) Cancelled intention executed (EAC)'),
                                          (b, 'exec_k', 'exec_n', 'EXEC (%)', '(b) Live intention executed (EXEC)')]:
    xs = []
    for i, (pol, lab, col) in enumerate(spec):
        for j, (mm, hatch) in enumerate([(m, None), (g, '////')]):
            if pol not in mm or mm[pol][key_n] == 0: continue
            k, n = mm[pol][key_k], mm[pol][key_n]; v = 100 * k / n; lo, hi = wilson(k, n)
            x = i + (-0.19 if j == 0 else 0.19)
            ax.bar(x, v, width=0.36, color=col, linewidth=0, hatch=hatch, edgecolor='white' if hatch else col)
            ax.errorbar(x, v, yerr=[[v - lo], [hi - v]], fmt='none', ecolor=INK, elinewidth=0.6)
            ax.text(x, hi + 1.5, f"{v:.0f}", ha='center', va='bottom', fontsize=5.6, color=INK)
    ax.set_xticks(range(len(spec))); ax.set_xticklabels([s[1] for s in spec], fontsize=6.4)
    style(ax, ylabel, 108); ax.set_title(title, loc='left', fontsize=8.5)
    ax.set_xlim(-0.6, len(spec) - 0.4)
for x in [0.5, 4.5, 5.5]:
    a.axvline(x, color=GRID, linewidth=0.8); b.axvline(x, color=GRID, linewidth=0.8)
for ax, y in [(a, 96), ]:
    ax.text(2.5, y, 'designs in common use', ha='center', va='bottom', fontsize=6.4, color=MUTED)
    ax.text(5.0, y, 'reference', ha='center', va='bottom', fontsize=6.4, color=MUTED)
    ax.text(7.0, y, 'self-kept ledger (no ground truth)', ha='center', va='bottom', fontsize=6.4, color=MUTED)
h = [Patch(facecolor='#777', label='GPT-4o-mini actor'), Patch(facecolor='#777', hatch='////', edgecolor='white', label='Gemini-2.5-Flash-Lite actor')]
fig.legend(handles=h, loc='lower center', ncol=2, frameon=False, fontsize=7, bbox_to_anchor=(0.5, -0.04))
fig.tight_layout(h_pad=0.4); save(fig, 'fig_ablation')

# ---------------------------------------------------------------- Fig: what is in the self-kept ledger, by step
spec_true = {}
for l in open('suite/epm_v0.1_thor.jsonl'):
    ep = json.loads(l)
    if ep['split'] == 'dev' and ep['delay'] == 6 and ep['load'] == 1:
        spec_true[(ep['seed'], ep['variant'])] = ep['spec']['intention']['trigger_type']
T = 40


def ledger_curves(tag, d='results/or_gpt4omini'):
    fab = [0] * T; acted = [0] * T; n_all = 0
    for f in glob.glob(f'{d}/*_{tag}.trace.jsonl'):
        mm = re.search(r'_s(\d+)_d6_l1_(\w+?)_llm-', f)
        if not mm: continue
        seed, var = int(mm.group(1)), mm.group(2)
        if (seed, var) not in spec_true: continue
        true = spec_true[(seed, var)]; rs = [json.loads(l) for l in open(f)]
        n_all += 1; first_act = None; seen_fab = set()
        for r in rs:
            t = r['t']
            if t >= T: continue
            note = str(r.get('note') or '')
            fabs = {x for x in re.findall(r'SEE the (\w+) ON', note) if x != true}
            seen_fab |= fabs
            if fabs: fab[t] += 1
            act = str(r.get('action', ''))
            if first_act is None and act.startswith('toggle_off') and act.split(' ', 1)[-1] in seen_fab:
                first_act = t
        if first_act is not None:
            for t in range(first_act, T): acted[t] += 1
    return [100 * x / n_all for x in fab], [100 * x / n_all for x in acted], n_all


fig, ax = plt.subplots(figsize=(3.3, 1.7))
GEM = '#1f9e89'
LEDGER_N = {}
for d, tag, lab, col, lw in [('results/or_deepseek', 'llm-rwim5', 'DeepSeek-V3', C['grey'], 1.2),
                             ('results/or_llama', 'llm-rwim5', 'Llama-3.3-70B', C['grey'], 1.2),
                             ('results/or_gpt4omini', 'llm-rwim5@claude-sonnet-', 'Sonnet 5', C['grey'], 1.2),
                             ('results/or_gemini', 'llm-rwim5', 'Gemini-2.5-FL', GEM, 1.8),
                             ('results/or_gpt4omini', 'llm-rwim5', 'GPT-4o-mini', C['rwim'], 1.8)]:
    fabc, actc, n_all = ledger_curves(tag, d); LEDGER_N[lab] = n_all
    ax.plot(range(T), fabc, color=col, linewidth=lw)
    ax.plot(range(T), actc, color=col, linewidth=max(1.0, lw - 0.4), linestyle='--')
print('fig_ledger episodes per bookkeeper:', LEDGER_N)
style(ax, '% of episodes', 70); ax.set_yticks([0, 20, 40, 60])
ax.set_xlim(0, T - 1); ax.set_xticks([0, 10, 20, 30, 39]); ax.set_xlabel('step', fontsize=7, labelpad=1)
h = [Line2D([0], [0], color=C['rwim'], linewidth=1.8, label='GPT-4o-mini keeps the ledger'),
     Line2D([0], [0], color=GEM, linewidth=1.8, label='Gemini-2.5-FL keeps it'),
     Line2D([0], [0], color=C['grey'], linewidth=1.2, label='DeepSeek-V3, Llama-3.3-70B, Sonnet 5: at 0')]
ax.legend(handles=h, loc='upper left', frameon=False, fontsize=5.6, handlelength=1.6)
fig.tight_layout(); save(fig, 'fig_ledger')

# ---------------------------------------------------------------- Fig: robustness (delay + Habitat)
fig, (a, b) = plt.subplots(1, 2, figsize=(3.3, 1.75), gridspec_kw={'width_ratios': [1.15, 1]})
xs = [3, 6, 10, 14]
for tag, ls in [('gpt4omini', '-'), ('gemini', '--')]:
    D = S['delay'][tag]
    for pol in ['bank', 'sched2']:
        ys = [100 * D[str(x)][pol]['eac_k'] / D[str(x)][pol]['eac_n'] if D[str(x)][pol]['eac_n'] else float('nan') for x in xs]
        a.plot(xs, ys, color=C[pol], linewidth=1.8, linestyle=ls, marker='o', markersize=3.5, markeredgecolor='white', markeredgewidth=0.8)
style(a, 'EAC (%)', 100); a.set_xticks(xs); a.set_xlim(2, 15)
a.set_xlabel('delay (steps)', fontsize=7, labelpad=1); a.set_title('(a) Delay', loc='left', fontsize=7)
h = [Line2D([0], [0], color=INK, linestyle='-', label='GPT-4o-mini'), Line2D([0], [0], color=INK, linestyle='--', label='Gemini')]
a.legend(handles=h, loc='center right', bbox_to_anchor=(1.02, 0.30), frameon=False, fontsize=5.4, handlelength=1.4)


def hab(f):
    rows = list(csv.DictReader(open(f))); out = {}
    for pol in ['llm-bank', 'llm-sched2']:
        ce = [r for r in rows if r['policy'] == pol and r['variant'] in ('cancel_early', 'cancel_late')]
        lv = [r for r in rows if r['policy'] == pol and r['variant'] == 'live']
        out[pol[4:]] = (sum(r['eac_strict'] == 'True' for r in ce), len(ce), sum(r['executed'] == 'True' for r in lv), len(lv))
    return out


H = {'Gemini\napt.': hab('results/hab_or_gemini.csv'), 'GPT-4o\nmini apt.': hab('results/hab_or_gpt4omini.csv'),
     'Gemini\ncastle': hab('results/hab_or_gemini_test.csv')}
for i, (lab, d) in enumerate(H.items()):
    for j, pol in enumerate(['bank', 'sched2']):
        k, n, ek, en = d[pol]; v = 100 * k / n; lo, hi = wilson(k, n); x = i + (-0.2 if j == 0 else 0.2)
        b.bar(x, max(v, 1.2), width=0.38, color=C[pol], linewidth=0)
        b.errorbar(x, v, yerr=[[v - lo], [hi - v]], fmt='none', ecolor=INK, elinewidth=0.6)
        b.text(x, hi + 1.5, f"{v:.0f}", ha='center', va='bottom', fontsize=5.6)
b.set_xticks(range(len(H))); b.set_xticklabels(list(H.keys()), fontsize=5.6)
style(b, '', 100); b.set_title('(b) Habitat', loc='left', fontsize=7)
hb = [Patch(color=C['bank'], label='raw store'), Patch(color=C['sched2'], label='status-tracked store')]
fig.legend(handles=hb, loc='lower center', ncol=2, frameon=False, fontsize=6, bbox_to_anchor=(0.5, -0.08), handlelength=1.2)
fig.tight_layout(w_pad=0.5); save(fig, 'fig_robust')
print('figs written to', OUT, ':', sorted(os.listdir(OUT)))
