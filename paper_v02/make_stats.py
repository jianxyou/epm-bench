"""Consolidate every number the v02 paper uses into paper_v02/stats.json."""
import csv, json, math, os, collections
R = 'results'
def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k/n; d = 1+z*z/n; c = (p+z*z/(2*n))/d; h = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (100*(c-h), 100*(c+h))
def load(tag):
    p = f'{R}/llm_or_{tag}.csv'
    rows = list(csv.DictReader(open(p))) if os.path.exists(p) else []
    # control twins: use ONLY the exposure-matched rerun (ctrl2, 2026-09-20).
    # The original control twins injected nothing and ended early (F42), so
    # their floor is biased; they are dropped wherever a ctrl2 file exists.
    p2 = f'{R}/llm_or_{tag}_ctrl2.csv'
    if os.path.exists(p2):
        c2 = list(csv.DictReader(open(p2))); fixed = {r['policy'] for r in c2}
        rows = [r for r in rows if not (r['variant'] == 'control' and r['policy'] in fixed)] + c2
    return rows
def cell(rows, pol, variants):
    xs = [r for r in rows if r['policy'] == pol and r['variant'] in variants]
    return xs
def summarize(rows, pol):
    ce = cell(rows, pol, {'cancel_early','cancel_late'})
    lv = cell(rows, pol, {'live'}); ct = cell(rows, pol, {'control'})
    k = sum(r['eac_strict']=='True' for r in ce)
    seen = [r for r in lv if r['first_visible_step'] != '']
    out = {'eac_k': k, 'eac_n': len(ce), 'eac': 100*k/len(ce) if ce else None,
           'eac_ci': wilson(k, len(ce)) if ce else None,
           'eac_early': (sum(r['eac_strict']=='True' for r in ce if r['variant']=='cancel_early'), sum(1 for r in ce if r['variant']=='cancel_early')),
           'eac_late': (sum(r['eac_strict']=='True' for r in ce if r['variant']=='cancel_late'), sum(1 for r in ce if r['variant']=='cancel_late')),
           'exec_k': sum(r['executed']=='True' for r in lv), 'exec_n': len(lv),
           'exec': 100*sum(r['executed']=='True' for r in lv)/len(lv) if lv else None,
           'ctrl_k': sum(r['executed']=='True' for r in ct), 'ctrl_n': len(ct),
           'ctrl': 100*sum(r['executed']=='True' for r in ct)/len(ct) if ct else None,
           'notice': 100*len(seen)/len(lv) if lv else None,
           'exec_given_seen': 100*sum(r['executed']=='True' for r in seen)/len(seen) if seen else None,
           'chores': sum(int(r['chores_done']) for r in ce+lv)/len(ce+lv) if ce+lv else None,
           'steps': sum(int(r['steps_total']) for r in ce+lv)/len(ce+lv) if ce+lv else None,
           'tok': sum(int(r['api_tokens']) for r in ce+lv)/len(ce+lv) if ce+lv else None}
    if out['exec'] is not None and out['ctrl'] is not None: out['mem'] = out['exec']-out['ctrl']
    return out
MODELS = [('gpt4omini','GPT-4o-mini'),('deepseek','DeepSeek-V3'),('llama','Llama-3.3-70B'),
          ('gemini','Gemini-2.5-Flash-Lite'),('sonnet5','Claude Sonnet 5'),('gpt55','GPT-5.5')]
POLS = ['llm-none','llm-bank','llm-retr','llm-retr2','llm-summ','llm-sched1','llm-sched1e','llm-sched',
        'llm-sched2','llm-rwim3','llm-rwim4','llm-rwim5',
        'llm-rwim4@claude-sonnet-','llm-rwim5@claude-sonnet-']
S = {'main': {}, 'delay': {}, 'heldout': {}, 'rgb': {}, 'totals': {}}
tot = 0
for tag, name in MODELS:
    rows = load(tag); tot += len(rows)
    S['main'][tag] = {'name': name, 'n_eps': len(rows)}
    for pol in POLS:
        if any(r['policy']==pol for r in rows):
            S['main'][tag][pol[4:]] = summarize(rows, pol)
for tag in ['gpt4omini','gemini']:
    rows = load(f'{tag}_delay') + [r for r in load(tag) if r['delay']=='6' and int(r['seed'])<20]
    tot += len(load(f'{tag}_delay'))
    S['delay'][tag] = {}
    for d in ['3','6','10','14']:
        S['delay'][tag][d] = {}
        for pol in ['llm-bank','llm-sched2']:
            ce=[r for r in rows if r['policy']==pol and r['delay']==d and r['variant']=='cancel_early']
            lv=[r for r in rows if r['policy']==pol and r['delay']==d and r['variant']=='live']
            S['delay'][tag][d][pol[4:]] = {'eac_k': sum(r['eac_strict']=='True' for r in ce), 'eac_n': len(ce),
                                           'exec_k': sum(r['executed']=='True' for r in lv), 'exec_n': len(lv)}
    rows = load(f'{tag}_test'); tot += len(rows)
    S['heldout'][tag] = {}
    for sc in ['FloorPlan2','FloorPlan3','FloorPlan4']:
        S['heldout'][tag][sc] = {}
        for pol in ['llm-bank','llm-sched2']:
            ce=[r for r in rows if r['policy']==pol and r['scene']==sc and r['variant']=='cancel_early']
            lv=[r for r in rows if r['policy']==pol and r['scene']==sc and r['variant']=='live']
            S['heldout'][tag][sc][pol[4:]] = {'eac_k': sum(r['eac_strict']=='True' for r in ce), 'eac_n': len(ce),
                                              'exec_k': sum(r['executed']=='True' for r in lv), 'exec_n': len(lv)}
    rows = load(f'{tag}_rgb'); tot += len(rows)
    S['rgb'][tag] = {}
    for pol in ['llm-bank-rgb','llm-sched2-rgb']:
        lv=[r for r in rows if r['policy']==pol and r['variant']=='live']; seen=[r for r in lv if r['first_visible_step']!='']
        ce=[r for r in rows if r['policy']==pol and r['variant']=='cancel_early']
        S['rgb'][tag][pol[4:-4]] = {'exec_k': sum(r['executed']=='True' for r in lv), 'exec_n': len(lv),
                                    'seen': len(seen), 'exec_seen': sum(r['executed']=='True' for r in seen),
                                    'eac_k': sum(r['eac_strict']=='True' for r in ce), 'eac_n': len(ce),
                                    'chores': sum(int(r['chores_done']) for r in lv)/len(lv) if lv else None}
# mechanical tier headline (suite_thor_v01.csv) for context
mech = list(csv.DictReader(open(f'{R}/suite_thor_v01.csv'))) if os.path.exists(f'{R}/suite_thor_v01.csv') else []
S['totals'] = {'llm_eps': tot, 'mech_eps': len(mech)}
json.dump(S, open('paper_v02/stats.json','w'), indent=1)
# quick print of the main table
print(f"LLM eps {tot}, mech eps {len(mech)}")
for tag,_ in MODELS:
    m=S['main'][tag]
    for pol in ['none','bank','retr','summ','sched1','sched2','rwim4','rwim5','rwim4@claude-sonnet-','rwim5@claude-sonnet-']:
        if pol in m:
            x=m[pol]; print(f"  {tag:<10}{pol:<22} EAC {x['eac_k']}/{x['eac_n']} ({x['eac']:.0f}%)  EXEC {x['exec_k']}/{x['exec_n']}  ctrl {x['ctrl_k']}/{x['ctrl_n']}")
