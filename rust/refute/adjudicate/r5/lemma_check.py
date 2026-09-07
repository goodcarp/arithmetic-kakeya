"""ADJUDICATION step 2: the two lemmas t3_check.py silently relies on, tested on
inputs where force() ACTUALLY SUCCEEDS (the t=3 sample was all-negative, so the
pairwise agreement there was vacuous).

L1: min_generators(rows,n,T0,pool,budget=0,mand=[]) == []   iff force(rows,n,T0) ok
    and == None otherwise.   (=> "r=0 hit" == "force succeeds")
L2: local_requirement(...)[0] == 0  iff  bad <= T0, where
    bad = {v : indep_dirs(inc[v])[0] < 2}.   (=> the P4 prune is exact, not heuristic)
L3: |bad| > t  =>  no 3-subset T0 contains bad  (skip whole graph is sound)
Sampled over the real cycles8 pattern set, T0 of EVERY size 0..8 so both
outcomes of force() are exercised.
"""
import sys, os, itertools, random, json
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","..","..","..","src")
sys.path.insert(0, os.path.abspath(SRC))
from kakeya import build_rows, ZERO
from search import POOL6, indep_dirs, local_requirement, min_generators
from fastcore import force
import cycles8 as C8
pool=POOL6; X=[ZERO]+list(pool); n=8
good=[]
for pattern in itertools.product([0,1],repeat=len(C8.SLOTS)):
    G=C8.build(pattern,[pool[0]]*sum(pattern),X)
    if G.m!=n: continue
    degs={v:0 for v in G.vertices()}
    for (u,v,x) in G.edges(): degs[u]+=1; degs[v]+=1
    if all(v==2 for v in degs.values()): good.append(pattern)
rng=random.Random(7); N=int(sys.argv[1]) if len(sys.argv)>1 else 600
l1_ok=l1_bad=0; l2_ok=l2_bad=0; l3_ok=l3_bad=0
force_true=0; force_false=0; mg_empty=0; mg_none=0; mt0=0
ex=[]
for _ in range(N):
    pattern=rng.choice(good); npres=sum(pattern)
    labels=tuple(rng.choice(pool) for _ in range(npres))
    G=C8.build(pattern,labels,X)
    base_rows,idx=build_rows(G,[])
    inc={j:[] for j in range(n)}
    for (u,v,x) in G.edges(): inc[idx[u]].append(x); inc[idx[v]].append(x)
    bad=frozenset(v for v in range(n) if indep_dirs(inc[v])[0]<2)
    k=rng.randint(0,8)
    T0=set(rng.sample(range(n),k))
    # L1
    mg=min_generators(base_rows,n,T0,pool,0,[])
    fok=force(base_rows,n,T0)[0]
    force_true+=fok; force_false+= (not fok)
    if mg==[]: mg_empty+=1
    if mg is None: mg_none+=1
    if (mg==[]) == fok and (mg is None) == (not fok): l1_ok+=1
    else:
        l1_bad+=1; ex.append(("L1",sorted(T0),mg,fok))
    # L2
    mt,_=local_requirement(G,idx,n,T0,pool)
    if mt==0: mt0+=1
    if (mt==0)==(bad<=T0): l2_ok+=1
    else: l2_bad+=1; ex.append(("L2",sorted(T0),mt,sorted(bad)))
    # L3 (t=3)
    if len(bad)>3:
        if any(bad<=set(c) for c in itertools.combinations(range(n),3)): l3_bad+=1
        else: l3_ok+=1
    else: l3_ok+=1
print("RESULT", json.dumps({"sampled":N,"L1_ok":l1_ok,"L1_violations":l1_bad,
 "L2_ok":l2_ok,"L2_violations":l2_bad,"L3_ok":l3_ok,"L3_violations":l3_bad,
 "force_true":force_true,"force_false":force_false,
 "min_gen_returned_empty":mg_empty,"min_gen_returned_None":mg_none,"mt_eq_0":mt0}))
for e in ex[:10]: print("VIOLATION",e)
