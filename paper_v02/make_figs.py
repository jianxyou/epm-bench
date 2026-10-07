"""Paper figures from paper_v02/stats.json. Palette: validated default (dataviz)."""
import json, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
S = json.load(open('paper_v02/stats.json'))
C = {'none':'#1baf7a','bank':'#eb6834','sched2':'#2a78d6','sched1':'#b5b3ab','sched':'#b5b3ab','rwim3':'#b5b3ab'}
INK, MUTED, GRID, BASE = '#0b0b0b', '#898781', '#e1e0d9', '#c3c2b7'
plt.rcParams.update({'font.family':'sans-serif','font.size':8,'axes.edgecolor':BASE,'axes.linewidth':0.8,
                     'xtick.color':MUTED,'ytick.color':MUTED,'axes.labelcolor':INK,'text.color':INK,
                     'axes.spines.top':False,'axes.spines.right':False,'ytick.major.width':0.6,'xtick.major.size':0})
def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (100*(c-h), 100*(c+h))
def style(ax, ylabel):
    ax.yaxis.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True)
    ax.set_ylim(0, 100); ax.set_yticks([0,25,50,75,100]); ax.set_ylabel(ylabel)
    ax.spines['left'].set_visible(False); ax.spines['bottom'].set_color(BASE)
def bars(ax, groups, pols, key_k, key_n, floor=None, label_caps=True):
    w = 0.26; gap = 0.03
    for gi, (tag, m) in enumerate(groups):
        for pi, pol in enumerate(pols):
            if pol not in m: continue
            x = gi + (pi - (len(pols)-1)/2) * (w + gap)
            k, n = m[pol][key_k], m[pol][key_n]
            if n == 0: continue
            v = 100*k/n; lo, hi = wilson(k, n)
            ax.bar(x, v, width=w, color=C[pol], linewidth=0)
            ax.errorbar(x, v, yerr=[[v-lo],[hi-v]], fmt='none', ecolor=INK, elinewidth=0.7, capsize=0)
            if label_caps:
                ax.text(x, hi+2, f"{v:.0f}", ha='center', va='bottom', fontsize=6.5, color=INK)
            if floor and m[pol].get(floor[1]):
                fk, fn = m[pol][floor[0]], m[pol][floor[1]]
                ax.plot([x-w/2, x+w/2], [100*fk/fn]*2, color=INK, linewidth=1.4, solid_capstyle='butt')
    SHORT = {'GPT-4o-mini':'GPT-4o\nmini','DeepSeek-V3':'DeepSeek\nV3','Llama-3.3-70B':'Llama-3.3\n70B','Gemini-2.5-Flash-Lite':'Gemini-2.5\nFlash-Lite','Claude Sonnet 5':'Claude\nSonnet 5','GPT-5.5':'GPT-5.5'}
    ax.set_xticks(range(len(groups))); ax.set_xticklabels([SHORT.get(m['name'], m['name']) for _, m in groups], fontsize=7)

# ---------- Fig 1: main result ----------
order = ['gpt4omini','deepseek','llama','gemini','sonnet5','gpt55']
groups = [(t, S['main'][t]) for t in order]
fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 2.15), gridspec_kw={'width_ratios':[6,4.2]})
bars(a, groups, ['none','bank','sched2'], 'eac_k', 'eac_n')
style(a, 'Cancelled intention executed (%)'); a.set_title('(a) After the user cancels', loc='left', fontsize=8.5, color=INK)
groups4 = [(t, S['main'][t]) for t in order[:4]]
bars(b, groups4, ['none','bank','sched2'], 'exec_k', 'exec_n', floor=('ctrl_k','ctrl_n'))
style(b, 'Live intention executed (%)'); b.set_title('(b) Live intention (no cancellation)', loc='left', fontsize=8.5, color=INK)
h = [Patch(color=C['none'], label='no store'), Patch(color=C['bank'], label='raw store'), Patch(color=C['sched2'], label='status-tracked store'),
     Line2D([0],[0], color=INK, linewidth=1.4, label='control-variant floor (no instruction)')]
fig.legend(handles=h, loc='lower center', ncol=4, frameon=False, fontsize=7, bbox_to_anchor=(0.5, -0.06))
fig.tight_layout(); fig.savefig('paper_v02/figs/fig_main.pdf', bbox_inches='tight'); fig.savefig('paper_v02/figs/fig_main.png', dpi=200, bbox_inches='tight')

# ---------- Fig 2: memory-representation ablation ----------
fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.3), sharey=True)
names = {'bank':'raw store','sched1':'status +\nrestated\nimperative','sched':'intention\nonly','sched2':'status-\ntracked','rwim3':'self-kept\nledger'}
for ax, tag, title in [(axes[0],'gpt4omini','(a) GPT-4o-mini'), (axes[1],'gemini','(b) Gemini-2.5-Flash-Lite')]:
    m = S['main'][tag]; pols = [p for p in ['bank','sched1','sched','sched2','rwim3'] if p in m]
    for i, pol in enumerate(pols):
        k, n = m[pol]['eac_k'], m[pol]['eac_n']; v = 100*k/n; lo, hi = wilson(k, n)
        ax.bar(i, v, width=0.55, color=C[pol], linewidth=0)
        ax.errorbar(i, v, yerr=[[v-lo],[hi-v]], fmt='none', ecolor=INK, elinewidth=0.7)
        ax.text(i, hi+2, f"{v:.0f}%\n(n={n})", ha='center', va='bottom', fontsize=6.3, color=INK)
    ax.set_xticks(range(len(pols))); ax.set_xticklabels([names[p] for p in pols], fontsize=6.8)
    style(ax, 'Cancelled intention executed (%)' if ax is axes[0] else ''); ax.set_title(title, loc='left', fontsize=8.5)
    ax.set_ylim(0, 105)
fig.tight_layout(); fig.savefig('paper_v02/figs/fig_ablation.pdf', bbox_inches='tight'); fig.savefig('paper_v02/figs/fig_ablation.png', dpi=200, bbox_inches='tight')

# ---------- Fig 3: delay sweep ----------
fig, axes = plt.subplots(2, 2, figsize=(6.6, 3.4), sharex=True)
for col, tag, title in [(0,'gpt4omini','GPT-4o-mini'), (1,'gemini','Gemini-2.5-Flash-Lite')]:
    D = S['delay'][tag]; xs = [3,6,10,14]
    for row, (kk, nn, ylabel) in enumerate([('eac_k','eac_n','Cancelled intention\nexecuted (%)'), ('exec_k','exec_n','Live intention\nexecuted (%)')]):
        ax = axes[row][col]
        for pol in ['bank','sched2']:
            ys = [100*D[str(x)][pol][kk]/D[str(x)][pol][nn] if D[str(x)][pol][nn] else float('nan') for x in xs]
            ax.plot(xs, ys, color=C[pol], linewidth=2, marker='o', markersize=5, markeredgecolor='white', markeredgewidth=1.2, solid_capstyle='round')
        style(ax, ylabel if col == 0 else ''); ax.set_xlim(2, 15); ax.set_xticks(xs)
        if row == 0: ax.set_title(title, loc='left', fontsize=8.5)
        if row == 1: ax.set_xlabel('Delay between briefing and trigger (steps)')
hd = [Line2D([0],[0], color=C['bank'], linewidth=2, marker='o', markersize=5, label='raw store'),
      Line2D([0],[0], color=C['sched2'], linewidth=2, marker='o', markersize=5, label='status-tracked store')]
fig.legend(handles=hd, loc='lower center', ncol=2, frameon=False, fontsize=7, bbox_to_anchor=(0.5, -0.04))
fig.tight_layout(); fig.savefig('paper_v02/figs/fig_delay.pdf', bbox_inches='tight'); fig.savefig('paper_v02/figs/fig_delay.png', dpi=200, bbox_inches='tight')
print("figs written: fig_main, fig_ablation, fig_delay (.pdf/.png)")
