#!/usr/bin/env python3
"""Audit of the self-kept ledger (rwim5) across bookkeeper models.
For every episode: which triggers did the bookkeeper ever write into the ledger, and did the actor
switch off an object that was the subject of no user instruction?
  fabricated entry = a ledger entry whose trigger is not the trigger of the user's instruction
                     (in the control variant the user gave no instruction, so every entry is fabricated)
  chore-derived    = the fabricated trigger is an object named in the chore list
  acted            = the actor executed toggle_off on a fabricated trigger
Traces store the bookkeeper's raw reply cut at 400 characters, so triggers are read with a regex."""
import json, os, re, collections, sys
SUITE = {}
for l in open('suite/epm_v0.1_thor.jsonl'):
    e = json.loads(l)
    if e['scene'] == 'FloorPlan1' and e['delay'] == 6 and e['load'] == 1:
        SUITE[(e['seed'], e['variant'])] = e['spec']
TRIG = re.compile(r'"trigger"\s*:\s*"([^"]+)"')
norm = lambda s: re.sub(r'[^a-z]', '', s.lower())

def audit(tag, pol='llm-rwim5', seeds=range(50)):
    out = collections.OrderedDict()
    for group, variants, d in (('instruction given', ('cancel_early', 'cancel_late', 'live'), f'results/or_{tag}'),
                               ('control (no instruction)', ('control',), f'results/or_{tag}_ctrl2')):
        c = collections.Counter(); examples = []
        for v in variants:
            for s in seeds:
                f = f'{d}/thor_FloorPlan1_s{s}_d6_l1_{v}_{pol}.trace.jsonl'
                if not os.path.exists(f) or (s, v) not in SUITE: continue
                spec = SUITE[(s, v)]; true = norm(spec['intention']['trigger_type']) if v != 'control' else None
                chore_objs = {norm(x) for ab in spec['chores'] for x in ab}
                fab = set(); acted = set(); parse_fail = 0
                for l in open(f):
                    r = json.loads(l)
                    raw = r.get('coroutine_raw')
                    if raw is not None:
                        if not r.get('parse_ok', True): parse_fail += 1
                        for t in TRIG.findall(raw):
                            if norm(t) and norm(t) != true: fab.add(norm(t))
                    a = (r.get('action') or '')
                    if a.startswith('toggle_off '):
                        x = norm(a.split(' ', 1)[1])
                        if x != true and x in fab: acted.add(x)
                c['episodes'] += 1
                c['with a fabricated entry'] += bool(fab)
                c['  of which chore-derived only'] += bool(fab) and fab <= chore_objs
                c['  of which includes a non-chore object'] += bool(fab - chore_objs)
                c['actor switched off a fabricated trigger'] += bool(acted)
                c['steps with unparseable ledger'] += parse_fail
                if fab and len(examples) < 2: examples.append((s, v, sorted(fab), sorted(acted)))
        out[group] = (c, examples)
    return out

if __name__ == '__main__':
    res = {}
    for tag, name, pol in (('gpt4omini', 'GPT-4o-mini', 'llm-rwim5'), ('gemini', 'Gemini-2.5-FL', 'llm-rwim5'),
                           ('deepseek', 'DeepSeek-V3', 'llm-rwim5'), ('llama', 'Llama-3.3-70B', 'llm-rwim5'),
                           ('gpt4omini', 'Sonnet 5 bookkeeper (actor mini)', 'llm-rwim5@claude-sonnet-')):
        a = audit(tag, pol); res[name] = {g: dict(c) for g, (c, _) in a.items()}
        print(f'\n=== bookkeeper: {name}')
        for g, (c, ex) in a.items():
            n = c['episodes']
            if not n: print(f'  {g}: no traces'); continue
            print(f'  {g}: {n} episodes')
            for k in ('with a fabricated entry', '  of which chore-derived only', '  of which includes a non-chore object', 'actor switched off a fabricated trigger'):
                print(f'     {c[k]:3d} ({100*c[k]/n:3.0f}%)  {k}')
            print(f'     unparseable ledger steps: {c["steps with unparseable ledger"]}   e.g. {ex[:2]}')
    json.dump(res, open('results/audit_ledger_all.json', 'w'), indent=1)
