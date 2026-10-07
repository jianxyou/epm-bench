#!/usr/bin/env python3
"""Six-intention columns of the main table (AI2-THOR, delay 6, load 6, seeds 0-49) from
results/llm_or_{tag}_load_v1obs.csv. EAC pools cancel-early and cancel-late over the seeds that have BOTH
(so a half-finished cell is not biased towards one variant); EXEC is the mean share of the six live
intentions carried out; floor is the share of control episodes in which the first trigger was switched off.
Half-up rounding. Prints LaTeX rows, paired exact McNemar tests, and writes results/load6_table_s50.json.
With --write it replaces the six-intention columns in sections/05_results.tex."""
import csv, json, math, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, '..', 'results')
MODELS = [('gpt4omini', 'GPT-4o-mini'), ('deepseek', 'DeepSeek-V3'), ('llama', 'Llama-3.3-70B'), ('gemini', 'Gemini-2.5-FL')]
DESIGNS = [('none', 'none'), ('bank', 'bank'), ('retr', 'retr'), ('summ', 'summ'), ('rwim5', 'rwim-ledger'), ('sched2', 'sched')]
def pct(k, n): return int(100 * k / n + 0.5) if n else None
def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n)
def first_off(tag, pol, r):
    """Control variant: was the first trigger (the one cancelled in the other variants) switched off? The csv's
    `executed` means all six at load 6, so read the per-intention verdict from the dump; fall back to exec_step."""
    f = os.path.join(RES, f'or_{tag}_load_v1obs', r['twin_group'].replace('/', '_') + f"_control_llm-{pol}.json")
    if os.path.exists(f):
        return bool(json.load(open(f))['adjudication']['per_intention'][0]['executed'])
    return r['exec_step'] not in ('', 'None')
def load(tag):
    D = collections.defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(RES, f'llm_or_{tag}_load_v1obs.csv'))):
        if r['load'] == '6' and r['delay'] == '6' and r['scene'] == 'FloorPlan1' and int(r['seed']) < 50:
            D[(r['policy'][4:], r['variant'])].setdefault(int(r['seed']), r)
    return D
def eac_by_seed(D, pol):
    e, l = D[(pol, 'cancel_early')], D[(pol, 'cancel_late')]
    return {s: (e[s]['eac_strict'] == 'True', l[s]['eac_strict'] == 'True') for s in e if s in l}
out, rows = {}, {}
for tag, mname in MODELS:
    D = load(tag); out[tag] = {}
    for pol, pname in DESIGNS:
        if any(len(D.get((pol, v), {})) < 10 for v in ('cancel_early', 'cancel_late', 'live', 'control')):
            continue      # not run for this actor (a stray partial cell counts as not run)
        E = eac_by_seed(D, pol); k = sum(a + b for a, b in E.values()); n = 2 * len(E)
        live = D[(pol, 'live')]; ctrl = D[(pol, 'control')]
        ex = 100 * sum(float(r['executed_frac']) for r in live.values()) / len(live)
        fl = sum(first_off(tag, pol, r) for r in ctrl.values())      # floor: the FIRST trigger switched off without instruction
        out[tag][pol] = dict(eac_k=k, eac_n=n, eac=pct(k, n), exec=int(ex + 0.5) if ex is not None else None, exec_n=len(live),
                             floor_k=fl, floor_n=len(ctrl), floor=pct(fl, len(ctrl)),
                             early=f"{sum(a for a, _ in E.values())}/{len(E)}", late=f"{sum(b for _, b in E.values())}/{len(E)}")
    for a, b in (('bank', 'sched2'), ('bank', 'rwim5'), ('rwim5', 'sched2')):
        if (a, 'cancel_early') in D and (b, 'cancel_early') in D:
            A, B = eac_by_seed(D, a), eac_by_seed(D, b); com = [s for s in A if s in B]
            ao = sum((A[s][i] and not B[s][i]) for s in com for i in (0, 1)); bo = sum((B[s][i] and not A[s][i]) for s in com for i in (0, 1))
            out[tag][f'{a}_vs_{b}'] = dict(a_only=ao, b_only=bo, seeds=len(com), p=mcnemar(ao, bo))
json.dump(out, open(os.path.join(RES, 'load6_table_s50.json'), 'w'), indent=1)
for tag, mname in MODELS:
    print(mname)
    for pol, pname in DESIGNS:
        d = out[tag].get(pol)
        if d: print(f"  {pname:12s} EAC {d['eac']:3d}% ({d['eac_k']}/{d['eac_n']}; early {d['early']}, late {d['late']}) | EXEC {d['exec']:3d}% (n={d['exec_n']}) | floor {d['floor']:3d}% ({d['floor_k']}/{d['floor_n']})")
    for k, v in out[tag].items():
        if '_vs_' in k: print(f"  {k}: {v['a_only']} vs {v['b_only']} on {v['seeds']} seeds (x2 variants), p={v['p']:.4f}")
# LaTeX
tex = os.path.join(HERE, 'sections', '05_results.tex'); s = open(tex).read()
a = s.index('\\begin{table}[t]'); b = s.index('\\end{table}'); tab = s[a:b]; cur = None; new = []
for ln in tab.split('\n'):
    m = re.search(r'\\multirow\{\d\}\{\*\}\{([^}]*)\}', ln)
    if m: cur = {n: t for t, n in MODELS}.get(m.group(1))
    m = re.match(r'(\s*& \\textsc\{([a-z-]+)\}\S*\s*&\s*[^&]*&\s*[^&]*&\s*[^&]*)&', ln)
    if m and cur:
        d = out[cur].get({n: p for p, n in DESIGNS}[m.group(2)])
        cells = ['--'] * 3 if not d else [f"{d['eac']}\\%", f"{d['exec']}\\%", f"{d['floor']}\\%"]
        if d and m.group(2) in ('bank', 'sched'): cells[0] = '\\textbf{' + cells[0] + '}'
        ln = m.group(1) + '& ' + ' & '.join(cells) + ' \\\\'
    new.append(ln)
tab = '\n'.join(new)
if '--write' in sys.argv:
    open(tex, 'w').write(s[:a] + tab + s[b:]); print('wrote six-intention columns into', tex)
else:
    print(tab)
