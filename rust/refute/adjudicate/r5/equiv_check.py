"""ADJUDICATION: is t3_check.py's hit criterion EXACTLY the driver's at t=3?

Driver path (src/cycles8.py, t=3):
    den=5; budget=int(target*den)-G.m; skip if budget<0 or den-rk>budget
    mt,mand = local_requirement(G,idx,n,T0,pool); skip if mt>budget
    gens = min_generators(base_rows,n,T0,pool,budget,mand)
    hit iff gens is not None and Fraction(m+len(gens),den) <= target

t3_check path:
    bad = {v : indep_dirs(inc[v])[0] < 2}; require bad<=T0; hit iff force(base_rows,n,T0)[0]

We run BOTH on a random sample of (graph,T0) pairs from the real pattern set and
assert they agree pair-by-pair.  We also report how often the driver's own
`den-rk>budget` prune would have SKIPPED a pair that t3_check still tested
(t3_check must be a superset, never a subset).
"""
import sys, os, itertools, random, json, time
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","..","..","..","src")
sys.path.insert(0, os.path.abspath(SRC))
from fractions import Fraction
from kakeya import build_rows, ZERO
from search import POOL6, indep_dirs, local_requirement, min_generators
from fastcore import force, rank
import cycles8 as C8

pool = POOL6; X = [ZERO]+list(pool); n = 8; t = 3
target = Fraction(67,40)

# budget arithmetic straight from the driver's formula, m=8
print("budget table (driver formula int(target*den) - G.m, m=8):")
for tt in range(0,7):
    den = n-tt
    b = int(target*den) - 8
    sc = Fraction(8+max(b,0), den) if den>0 else None
    print("  t=%d den=%d int(67/40*%d)=%d budget=%d  score_at_r0=%s (<=target: %s)"
          % (tt, den, den, int(target*den), b, Fraction(8,den) if den else None,
             (Fraction(8,den) <= target) if den else None))

good=[]
for pattern in itertools.product([0,1],repeat=len(C8.SLOTS)):
    G=C8.build(pattern,[pool[0]]*sum(pattern),X)
    if G.m!=n: continue
    degs={v:0 for v in G.vertices()}
    for (u,v,x) in G.edges(): degs[u]+=1; degs[v]+=1
    if all(v==2 for v in degs.values()): good.append(pattern)
print("patterns:", good)

T0S=list(itertools.combinations(range(n),t))
rng=random.Random(20260906)
N=int(sys.argv[1]) if len(sys.argv)>1 else 400
agree=0; disagree=[]; drv_hits=0; chk_hits=0
prune_would_skip=0; prune_skip_and_chk_tested=0
t0=time.time()
for _ in range(N):
    pattern=rng.choice(good); npres=sum(pattern)
    labels=tuple(rng.choice(pool) for _ in range(npres))
    G=C8.build(pattern,labels,X)
    base_rows,idx=build_rows(G,[])
    rk=rank(base_rows)
    den=n-t; budget=int(target*den)-G.m
    inc={j:[] for j in range(n)}
    for (u,v,x) in G.edges(): inc[idx[u]].append(x); inc[idx[v]].append(x)
    bad=frozenset(v for v in range(n) if indep_dirs(inc[v])[0]<2)
    pruned = (budget<0) or (den-rk>budget)
    if pruned: prune_would_skip+=1
    T0t=rng.choice(T0S); T0=set(T0t)
    # --- driver
    mt,mand=local_requirement(G,idx,n,T0,pool)
    if budget<0 or mt>budget:
        drv=False
    else:
        gens=min_generators(base_rows,n,T0,pool,budget,mand)
        drv = gens is not None and Fraction(G.m+len(gens),den)<=target
    # --- t3_check
    if not bad<=T0:
        chk=False
    else:
        chk=force(base_rows,n,T0)[0]
    if pruned and chk: prune_skip_and_chk_tested+=1
    if drv==chk: agree+=1
    else: disagree.append((pattern,labels,sorted(T0),drv,chk,mt,budget))
    drv_hits+=drv; chk_hits+=chk
print("RESULT", json.dumps({"sampled":N,"agree":agree,"disagree":len(disagree),
      "driver_hits":drv_hits,"t3check_hits":chk_hits,
      "pairs_driver_rk_prune_would_skip":prune_would_skip,
      "of_those_t3check_would_have_called_a_hit":prune_skip_and_chk_tested,
      "seconds":round(time.time()-t0,1)}))
for d in disagree[:10]: print("DISAGREE", d)
