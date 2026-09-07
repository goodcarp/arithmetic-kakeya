"""ADJUDICATION step 3: verify t3_check.py's graphs / skipped_by_P4 / pairs counts
for ALL five patterns without calling force() (force is the expensive part;
counting is cheap and is what the finding's coverage arithmetic rests on)."""
import sys, os, itertools, json, time
SRC=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","..","..","src")
sys.path.insert(0,os.path.abspath(SRC))
from kakeya import build_rows, ZERO
from search import POOL6, indep_dirs
import cycles8 as C8
pool=POOL6; X=[ZERO]+list(pool); n=8; t=3
good=[]
for p in itertools.product([0,1],repeat=len(C8.SLOTS)):
    G=C8.build(p,[pool[0]]*sum(p),X)
    if G.m!=n: continue
    degs={v:0 for v in G.vertices()}
    for (u,v,x) in G.edges(): degs[u]+=1; degs[v]+=1
    if all(v==2 for v in degs.values()): good.append(p)
def cycles(G):
    par=list(range(n))
    def find(a):
        while par[a]!=a: par[a]=par[par[a]]; a=par[a]
        return a
    idx={v:i for i,v in enumerate(sorted(G.vertices()))}
    for (u,v,x) in G.edges():
        a,b=find(idx[u]),find(idx[v])
        if a!=b: par[a]=b
    return len({find(i) for i in range(n)})
T0S=list(itertools.combinations(range(n),t))
tot={}
t0=time.time()
for i,p in enumerate(good):
    G0=C8.build(p,[pool[0]]*sum(p),X); kind="8cycle" if cycles(G0)==1 else "4+4"
    npres=sum(p); g=0; pr=0; sk=0
    for labels in itertools.product(pool,repeat=npres):
        G=C8.build(p,labels,X); g+=1
        base_rows,idx=build_rows(G,[])
        inc={v:[] for v in range(n)}
        for (u,v,x) in G.edges(): inc[idx[u]].append(x); inc[idx[v]].append(x)
        bad=frozenset(v for v in range(n) if indep_dirs(inc[v])[0]<2)
        if len(bad)>t: sk+=1; continue
        pr+=sum(1 for c in T0S if bad<=set(c))
    tot[i]=(kind,g,sk,pr)
    print("pattern",i,p,kind,"graphs",g,"skipped_P4",sk,"pairs",pr,flush=True)
print("RESULT",json.dumps({
 "8cycle_idx2_3":{"graphs":tot[2][1]+tot[3][1],"skipped":tot[2][2]+tot[3][2],"pairs":tot[2][3]+tot[3][3]},
 "idx1_4":{"graphs":tot[1][1]+tot[4][1],"skipped":tot[1][2]+tot[4][2],"pairs":tot[1][3]+tot[4][3]},
 "idx0":{"graphs":tot[0][1],"skipped":tot[0][2],"pairs":tot[0][3]},
 "all_five":{"graphs":sum(v[1] for v in tot.values()),"pairs":sum(v[3] for v in tot.values())},
 "seconds":round(time.time()-t0,1)}))
