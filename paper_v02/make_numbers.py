"""Emit paper_v02/numbers.tex: one macro per number the prose cites."""
import json, math
S = json.load(open('paper_v02/stats.json'))
def fisher(a,b,c,d):
    n=a+b+c+d; r1=a+b; c1=a+c
    def p(x): return math.comb(r1,x)*math.comb(n-r1,c1-x)/math.comb(n,c1)
    po=p(a); return sum(p(x) for x in range(max(0,c1-(n-r1)),min(r1,c1)+1) if p(x)<=po+1e-12)
def sci(p):
    if p >= 0.01: return f"{p:.2f}"
    e = int(math.floor(math.log10(p))); m = p/10**e
    return f"{m:.0f}\\times 10^{{{e}}}"
L = []
def m(name, val): L.append(f"\\newcommand{{\\{name}}}{{{val}}}")
tags = {'gpt4omini':'Mini','deepseek':'Deepseek','llama':'Llama','gemini':'Gemini','sonnet5':'Sonnet','gpt55':'Gptff'}
pols = {'none':'None','bank':'Bank','sched1':'Schedone','sched':'Sched','sched2':'Schedtwo','rwim3':'Rwim'}
for tag, T in tags.items():
    for pol, P in pols.items():
        x = S['main'][tag].get(pol)
        if not x: continue
        m(f"eac{T}{P}", f"{x['eac_k']}/{x['eac_n']}"); m(f"eacPct{T}{P}", f"{x['eac']:.0f}")
        if x['eac_ci']: m(f"eacCI{T}{P}", f"[{x['eac_ci'][0]:.0f},{x['eac_ci'][1]:.0f}]")
        if x['exec_n']: m(f"exec{T}{P}", f"{x['exec_k']}/{x['exec_n']}"); m(f"execPct{T}{P}", f"{x['exec']:.0f}")
        if x['ctrl_n']: m(f"ctrl{T}{P}", f"{x['ctrl_k']}/{x['ctrl_n']}"); m(f"ctrlPct{T}{P}", f"{x['ctrl']:.0f}")
        if x['notice'] is not None: m(f"notice{T}{P}", f"{x['notice']:.0f}")
        if x['exec_given_seen'] is not None: m(f"execSeen{T}{P}", f"{x['exec_given_seen']:.0f}")
        if x['tok']: m(f"tok{T}{P}", f"{x['tok']/1000:.0f}")
        if x['chores']: m(f"chores{T}{P}", f"{x['chores']:.1f}")
mi = S['main']['gpt4omini']
b, s2, s1 = mi['bank'], mi['sched2'], mi['sched1']
m("pBankSchedtwoMini", sci(fisher(b['eac_k'], b['eac_n']-b['eac_k'], s2['eac_k'], s2['eac_n']-s2['eac_k'])))
m("pSchedoneSchedtwoMini", sci(fisher(s1['eac_k'], s1['eac_n']-s1['eac_k'], s2['eac_k'], s2['eac_n']-s2['eac_k'])))
m("pBankSchedoneMini", sci(fisher(b['eac_k'], b['eac_n']-b['eac_k'], s1['eac_k'], s1['eac_n']-s1['eac_k'])))
g = S['main']['gemini']; gb, gs2, gs1 = g['bank'], g['sched2'], g['sched1']
m("pSchedoneSchedtwoGemini", sci(fisher(gs1['eac_k'], gs1['eac_n']-gs1['eac_k'], gs2['eac_k'], gs2['eac_n']-gs2['eac_k'])))
m("nLLMeps", f"{S['totals']['llm_eps']:,}"); m("nMechEps", f"{S['totals']['mech_eps']:,}")
for tag, T in [('gpt4omini','Mini'),('gemini','Gemini')]:
    for sc in ['FloorPlan2','FloorPlan3','FloorPlan4']:
        for pol, P in [('bank','Bank'),('sched2','Schedtwo')]:
            x = S['heldout'][tag][sc][pol]
            W = {'2':'Two','3':'Three','4':'Four'}[sc[-1]]
            m(f"ho{T}{W}{P}", f"{x['eac_k']}/{x['eac_n']}"); m(f"hoExec{T}{W}{P}", f"{x['exec_k']}/{x['exec_n']}")
    for pol, P in [('bank','Bank'),('sched2','Schedtwo')]:
        x = S['rgb'][tag][pol]
        m(f"rgbExecSeen{T}{P}", f"{x['exec_seen']}/{x['seen']}"); m(f"rgbExec{T}{P}", f"{x['exec_k']}/{x['exec_n']}"); m(f"rgbChores{T}{P}", f"{x['chores']:.1f}")
open('paper_v02/numbers.tex','w').write("\n".join(L)+"\n")
print(len(L), "macros;", "p(bank vs sched2, mini) =", [l for l in L if 'pBankSchedtwoMini' in l][0])
