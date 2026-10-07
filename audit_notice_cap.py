"""Audit: at the step the grader credits as first-visible, does observe() (14-object cap, alphabetical)
actually contain the trigger? Replays recorded gpt-4o-mini episodes in AI2-THOR."""
import json, glob, re, csv, sys
import numpy as np
from env import ThorPMEnv
spec={}
for l in open('suite/epm_v0.1_thor.jsonl'):
    e=json.loads(l)
    if e['split']=='dev' and e['delay']==6 and e['load']==1 and e['scene']=='FloorPlan1': spec[(e['seed'],e['variant'])]=e
rows=[r for r in csv.DictReader(open('results/llm_or_gpt4omini.csv')) if r['delay']=='6' and r['load']=='1' and r['split']=='dev'
      and r['policy'] in ('llm-bank','llm-sched2') and r['variant']=='cancel_early' and int(r['seed'])<20 and r['first_visible_step']!='']
env=ThorPMEnv(size=320); out=[]
try:
    for r in rows:
        seed=int(r['seed']); e=spec[(seed,'cancel_early')]; sp=dict(e['spec']); sp['chores']=[tuple(c) for c in sp['chores']]
        trig=sp['intention']['trigger_type']; tfirst=int(r['first_visible_step'])
        tr=[json.loads(l) for l in open(glob.glob(f"results/or_gpt4omini/*_s{seed}_d6_l1_cancel_early_{r['policy']}.trace.jsonl")[0])]
        env.reset(sp, scene='FloorPlan1'); rec=None
        for x in tr:
            if env.t==tfirst:
                obs=env.observe(); vis=[o for o in env.objects() if o['visible']]
                rec={'seed':seed,'policy':r['policy'],'t':tfirst,'trigger':trig,'in_text':(trig+' (ON)') in obs,
                     'n_visible':len(vis),'thor_says_visible':any(o['objectType']==trig and o['visible'] for o in vis)}
                break
            a=str(x['action']).split(' ',1); env.act(a[0], a[1] if len(a)>1 else None)
            if a[0]=='done': break
        if rec: out.append(rec); print(rec, flush=True)
finally:
    env.stop()
json.dump(out, open('results/audit_notice_cap.json','w'), indent=1)
n=len(out); cut=sum(1 for o in out if o['thor_says_visible'] and not o['in_text'])
print(f"\n{n} 集：THOR 说可见但文字里没有的 {cut} 集；平均可见物体数 {np.mean([o['n_visible'] for o in out]):.1f}")
