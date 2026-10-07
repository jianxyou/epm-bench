#!/usr/bin/env python3
"""Load curve figure (fig_load): commission (EAC, cancel-early) and execution (EXEC, live)
as the number of standing intentions grows from 1 to 6. GPT-4o-mini actor, AI2-THOR
FloorPlan1, delay 6. Loads 4-6 are taken only from the v0.1-ordering rerun
(results/llm_or_gpt4omini_load_v1obs.csv); the earlier load-4 run used a different
observation ordering and is excluded. Also prints the table and paired tests."""
import csv, glob, math, collections, os, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', 'results')
OUT = os.path.join(HERE, 'figs')
V1OBS = os.path.join(RES, 'llm_or_gpt4omini_load_v1obs.csv')

INK, MUTED, BASE, GRID = '#2b2b2b', '#6e6e6e', '#9a9a9a', '#e6e6e6'
C = {'bank': '#eb6834', 'sched2': '#2a78d6', 'rwim5': '#8e5bd6', 'retr': '#b5b3ab', 'summ': '#7a7a7a', 'retr2': '#b5b3ab'}
LABEL = {'bank': 'raw store (re-injected briefing)', 'retr': 'retrieval', 'summ': 'rolling summary',
         'sched2': 'status-tracked, rewritten on cancel', 'rwim5': 'self-kept ledger (mini bookkeeper)',
         'retr2': 'rewritten entry in retrieval store'}
STYLE = {'bank': dict(marker='D', ls='-'), 'sched2': dict(marker='o', ls='-'), 'rwim5': dict(marker='s', ls='-'),
         'retr': dict(marker='^', ls='--'), 'summ': dict(marker='v', ls=':'), 'retr2': dict(marker='x', ls='--')}
plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 8, 'axes.edgecolor': BASE, 'axes.linewidth': 0.8,
                     'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.labelcolor': INK, 'text.color': INK,
                     'legend.frameon': False, 'legend.fontsize': 6.4})


def wilson(k, n, z=1.96):
    if n == 0:
        return (float('nan'),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * p, 100 * (c - h), 100 * (c + h)


def load_rows():
    rows = {}
    files = sorted(glob.glob(os.path.join(RES, 'llm_or_gpt4omini*.csv')))
    files = [V1OBS] + [f for f in files if os.path.abspath(f) != os.path.abspath(V1OBS)]  # v1obs wins on duplicates
    for p in files:
        for r in csv.DictReader(open(p)):
            if r['engine'] != 'thor' or r['scene'] != 'FloorPlan1' or r['delay'] != '6':
                continue
            if r['variant'] not in ('cancel_early', 'live'):
                continue
            if int(r['load']) >= 4 and os.path.abspath(p) != os.path.abspath(V1OBS):
                continue  # old load-4 run: different observation ordering
            key = (r['policy'], r['twin_group'], r['variant'])
            rows.setdefault(key, r)
    return list(rows.values())


GEM_FILES = ['llm_or_gemini.csv', 'llm_or_gemini_load.csv', 'llm_or_gemini_load_v1obs.csv']


def load_gemini():
    rows = {}
    for f in GEM_FILES:
        p = os.path.join(RES, f)
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p)):
            if r['engine'] != 'thor' or r['scene'] != 'FloorPlan1' or r['delay'] != '6':
                continue
            if r['variant'] != 'cancel_early' or r['policy'] not in ('llm-bank', 'llm-sched2') or int(r['seed']) >= 20:
                continue
            rows.setdefault((r['policy'], r['twin_group']), r)
    return list(rows.values())


def curve(tag):
    """BANK, SCHED and RWIM-LEDGER for one actor, all seeds below 50. One intention from the main csv (the numbers of
    the main table), two and three from the load runs, four to six only from the v0.1-ordering rerun."""
    rows = {}
    for f, ok in ((f'llm_or_{tag}.csv', {1}), (f'llm_or_{tag}_load_v1obs.csv', {2, 3, 4, 5, 6}), (f'llm_or_{tag}_load.csv', {2, 3})):
        p = os.path.join(RES, f)
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p)):
            if r['engine'] != 'thor' or r['scene'] != 'FloorPlan1' or r['delay'] != '6' or int(r['load']) not in ok:
                continue
            if r['variant'] not in ('cancel_early', 'live') or r['policy'] not in ('llm-bank', 'llm-sched2', 'llm-rwim5') or int(r['seed']) >= 50:
                continue
            rows.setdefault((r['policy'], r['twin_group'], r['variant']), r)
    eac, exe = collections.defaultdict(list), collections.defaultdict(list)
    for r in rows.values():
        k = (r['policy'].replace('llm-', ''), int(r['load']))
        if r['variant'] == 'cancel_early':
            eac[k].append(r['eac_strict'] == 'True')
        else:
            exe[k].append(float(r['executed_frac']))
    return eac, exe


def cells(rows):
    eac, exe = collections.defaultdict(list), collections.defaultdict(list)
    for r in rows:
        pol = r['policy'].replace('llm-', '')
        L = int(r['load'])
        if int(r['seed']) >= (40 if pol in ('bank', 'sched2') else 20):
            continue      # same seeds at every load: 0-39 for bank/sched2, 0-19 otherwise (as in the caption)
        if r['variant'] == 'cancel_early':
            eac[(pol, L)].append(r['eac_strict'] == 'True')
        else:
            exe[(pol, L)].append(float(r['executed_frac']))
    return eac, exe


def main():
    rows = load_rows()
    eac, exe = cells(rows)
    designs = ['bank', 'retr', 'summ', 'sched2', 'rwim5']
    loads = range(1, 7)

    print('EAC cancel-early, % (n)')
    for d in designs + ['retr2']:
        print(f'  {d:7s}', ' | '.join(f'{wilson(sum(v), len(v))[0]:3.0f} ({len(v):2d})' if (v := eac.get((d, L))) else '   --   ' for L in loads))
    print('EXEC live, mean fraction of live intentions executed, % (n)')
    for d in designs:
        print(f'  {d:7s}', ' | '.join(f'{100 * sum(v) / len(v):3.0f} ({len(v):2d})' if (v := exe.get((d, L))) else '   --   ' for L in loads))

    # paired bank vs sched2 on common seeds
    bank = {(int(r['seed']), int(r['load'])): r['eac_strict'] == 'True' for r in rows if r['policy'] == 'llm-bank' and r['variant'] == 'cancel_early'}
    sch = {(int(r['seed']), int(r['load'])): r['eac_strict'] == 'True' for r in rows if r['policy'] == 'llm-sched2' and r['variant'] == 'cancel_early'}
    print('paired bank vs sched2 (bank-only / sched2-only / n), exact McNemar p')
    for L in loads:
        ks = [k for k in bank if k[1] == L and k in sch]
        b = sum(bank[k] and not sch[k] for k in ks); c = sum(sch[k] and not bank[k] for k in ks)
        n = b + c
        p = min(1.0, 2 * sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n) if n else 1.0
        print(f'  L{L}: {b} / {c} / n={len(ks)}  p={p:.3f}')

    # ---- figure: 2x2. Columns = the two designs that solve the one-intention case, rows = metric,
    # two lines per panel = the two actors (the designs tie within an actor, so they get separate panels) ----
    DES = [('sched2', 'SCHED'), ('rwim5', 'RWIM-LEDGER')]
    ACT = [('gpt4omini', dict(ls='-', hollow=False, lw=1.5)), ('gemini', dict(ls='--', hollow=True, lw=1.2))]
    data = {tag: curve(tag) for tag, _ in ACT}
    for tag, _ in ACT:
        e, x = data[tag]
        for d in ['bank', 'sched2', 'rwim5']:      # bank printed for the text only
            print(f'FIG {tag:9s} {d:6s} EAC early', [f"{wilson(sum(e[(d, L)]), len(e[(d, L)]))[0]:.0f}({len(e[(d, L)])})" for L in loads if (d, L) in e],
                  '| EXEC live', [f"{100 * sum(x[(d, L)]) / len(x[(d, L)]):.0f}({len(x[(d, L)])})" for L in loads if (d, L) in x])
    # default: SCHED only, EAC and EXEC side by side. With --with-ledger: 2x2, one column per design.
    if '--with-ledger' not in sys.argv:
        DES = DES[:1]
        fig, row = plt.subplots(1, 2, figsize=(3.3, 1.75))
        axs = [[row[0]], [row[1]]]
    else:
        fig, axs = plt.subplots(2, 2, figsize=(3.3, 2.6), sharex=True, sharey='row')
    wide = len(DES) > 1
    for j, (d, name) in enumerate(DES):
        a, b = axs[0][j], axs[1][j]
        for ax in (a, b):
            ax.yaxis.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True)
            for sp in ('top', 'right', 'left'):
                ax.spines[sp].set_visible(False)
            ax.set_xticks(list(loads)); ax.set_xlim(0.6, 6.4)
            ax.tick_params(length=2, labelsize=7)
        a.set_ylim(-4, 60); a.set_yticks([0, 20, 40, 60]); b.set_ylim(-6, 100); b.set_yticks([0, 50, 100])   # room below 0 so a point at 0% is not cut in half
        if wide:
            a.set_title(name, fontsize=8, color=C[d], fontweight='bold', pad=3)
        for tag, st in ACT:
            e, x = data[tag]
            kw = dict(color=C[d], ms=3.6, marker='o', ls=st['ls'], lw=st['lw'], mfc='white' if st['hollow'] else C[d],
                      capsize=0, elinewidth=0.5)
            xs = [L for L in loads if (d, L) in e]
            v = [wilson(sum(e[(d, L)]), len(e[(d, L)])) for L in xs]
            a.errorbar(xs, [q[0] for q in v], yerr=[[q[0] - q[1] for q in v], [min(q[2], 60) - q[0] for q in v]], **kw)
            xs = [L for L in loads if (d, L) in x]
            m = [100 * sum(x[(d, L)]) / len(x[(d, L)]) for L in xs]
            se = [100 * 1.96 * (sum((q - sum(x[(d, L)]) / len(x[(d, L)])) ** 2 for q in x[(d, L)]) / (len(x[(d, L)]) - 1)) ** 0.5
                  / len(x[(d, L)]) ** 0.5 for L in xs]
            b.errorbar(xs, m, yerr=se, **kw)
    h = [Line2D([], [], color=INK, marker='o', ms=3.6, lw=1.5, ls='-', label='GPT-4o-mini'),
         Line2D([], [], color=INK, marker='o', ms=3.6, lw=1.2, ls='--', mfc='white', label='Gemini 2.5 Flash Lite')]
    if wide:
        axs[0][0].set_ylabel('EAC (%)', fontsize=7.5); axs[1][0].set_ylabel('EXEC (%)', fontsize=7.5)
        axs[0][0].text(0.03, 0.93, 'lower is better', transform=axs[0][0].transAxes, fontsize=5.8, color=MUTED, va='top')
        axs[1][0].text(0.97, 0.93, 'higher is better', transform=axs[1][0].transAxes, fontsize=5.8, color=MUTED, va='top', ha='right')
        fig.tight_layout(h_pad=1.9, w_pad=0.8, rect=(0, 0.2, 1, 1))
        y0 = axs[1][0].get_position().y0
        fig.text(0.54, y0 - 0.125, 'number of standing intentions', ha='center', va='top', fontsize=7.5)
        fig.legend(handles=h, loc='upper center', ncol=2, handlelength=2.6, fontsize=6.5, bbox_to_anchor=(0.54, y0 - 0.19), columnspacing=1.6)
    else:
        a, b = axs[0][0], axs[1][0]
        a.set_title('(a) EAC (%), lower is better', loc='left', fontsize=7); b.set_title('(b) EXEC (%), higher is better', loc='left', fontsize=7)
        fig.tight_layout(w_pad=1.2, rect=(0, 0.25, 1, 1))
        y0 = a.get_position().y0
        fig.text(0.52, y0 - 0.14, 'number of standing intentions', ha='center', va='top', fontsize=7.5)
        fig.legend(handles=h, loc='upper center', ncol=2, handlelength=2.6, fontsize=6.5, bbox_to_anchor=(0.52, y0 - 0.235), columnspacing=1.6)
    name = 'fig_load_ledger' if wide else 'fig_load'      # the paper uses fig_load (SCHED only)
    fig.savefig(f'{OUT}/{name}.pdf', bbox_inches='tight'); fig.savefig(f'{OUT}/{name}.png', dpi=200, bbox_inches='tight')
    print('wrote', f'{OUT}/{name}.pdf')


if __name__ == '__main__':
    main()
