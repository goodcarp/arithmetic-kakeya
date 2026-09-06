"""Deeper exhaustive differential: 3-row ragged rank (zip-truncation cascade),
multi-restart force, warm-start chains, tuple/bool/range argument shapes."""
import itertools, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import fastcore, fastcore_rs
PY_F = fastcore._force_py; PY_R = fastcore._rank_py
RS_F = fastcore_rs.force;  RS_R = fastcore_rs.rank
def cpy(fn,*a):
    fastcore._INV.clear()
    try: return ("ok", fn(*a))
    except Exception as e: return ("exc", type(e).__name__)
def crs(fn,*a):
    try: return ("ok", fn(*a))
    except Exception as e: return ("exc", type(e).__name__)
def nf(t):
    k,v=t
    if k=="exc": return ("exc",v)
    ok,T=v; return ("ok",bool(ok),tuple(sorted(T)))
def nr(t):
    k,v=t
    if k=="exc": return ("exc",v)
    return ("ok",int(v))
bad=[]; cases=0
def chk(kind,args):
    global cases; cases+=1
    if kind=="force": a=nf(cpy(PY_F,*args)); b=nf(crs(RS_F,*args))
    else: a=nr(cpy(PY_R,*args)); b=nr(crs(RS_R,*args))
    if a!=b and len(bad)<40: bad.append((kind,args,a,b))
t=time.time()

# --- A: 3-row ragged rank, exhaustive over lengths 0..3, entries {0,1,2} -----
R=[]
for L in range(4):
    for tup in itertools.product([0,1,2],repeat=L): R.append(list(tup))
print("A rows:",len(R))
for p in (2,3,4,7):
    for r1 in R:
        for r2 in R:
            for r3 in R:
                chk("rank",([r1,r2,r3],p))
print("A done %d %.1fs bad=%d"%(cases,time.time()-t,len(bad)))

# --- B: multi-restart force, n=3, width 6, entries {0,1,-1}, 2-3 rows -------
W=[]
for tup in itertools.product([0,1,-1],repeat=6): W.append(list(tup))
print("B rows:",len(W))
import random
rng=random.Random(4242)
for p in (2,3,7,2147483647):
    for _ in range(4000):
        k=rng.randint(1,4)
        rows=[rng.choice(W) for _ in range(k)]
        T0=rng.choice([set(),{0},{1},{2},{0,1}])
        chk("force",(rows,3,T0,p))
        chk("rank",(rows,p))
print("B done %d %.1fs bad=%d"%(cases,time.time()-t,len(bad)))

# --- C: warm-start chains (the search.min_generators pattern) ---------------
for p in (3,7,2147483647):
    for _ in range(3000):
        rows=[rng.choice(W) for _ in range(rng.randint(0,3))]
        T=set()
        for _ in range(4):
            cases+=1
            fastcore._INV.clear()
            try: pa=("ok",PY_F(rows,3,T,p))
            except Exception as e: pa=("exc",type(e).__name__)
            try: rb=("ok",RS_F(rows,3,T,p))
            except Exception as e: rb=("exc",type(e).__name__)
            if nf(pa)!=nf(rb) and len(bad)<40: bad.append(("force-warm",(rows,3,sorted(T),p),nf(pa),nf(rb))); break
            if pa[0]=="exc": break
            ok,T2=pa[1]
            if ok: break
            T=set(T2); rows=rows+[rng.choice(W)]
print("C done %d %.1fs bad=%d"%(cases,time.time()-t,len(bad)))

# --- D: argument shapes: tuples, bools, range, frozenset, nested tuples -----
shapes=[
 (( (1,-1,0,0), (0,0,1,-1) ), 2, ()),
 ([ (1,-1,0,0), [0,0,1,-1] ], 2, frozenset()),
 ([[True,False,0,0],[0,0,True,False]], 2, set()),
 ([[1,-1,0,0],[0,0,1,-1]], 2, range(0,1)),
 ([[1,-1,0,0],[0,0,1,-1]], 2, (x for x in [])),
 ([[1,-1,0,0],[0,0,1,-1]], 2, iter([0])),
 ([[1,-1]], 2, {1}),
 ([[1,-1]], 1, {True}),
 ([[1,-1]], True, set()),
 ([], 1, []),
 ([[]], 1, []),
]
for rows,n,T0 in shapes:
    if hasattr(T0,'__next__'):
        # generators are single-use: build twice
        continue
    chk("force",(rows,n,T0,2147483647))
for rows in ([(1,2),(3,4)], [[True,True]], [[1],[2,3]], [[1,2,3],[4,5]], [[0,2],[1]],
             [[],[1,2]], [[1,1]]*1000, ((1,0),(0,1))):
    chk("rank",(rows,2147483647))
print("D done %d %.1fs bad=%d"%(cases,time.time()-t,len(bad)))

print("="*60); print("total %d mismatches %d"%(cases,len(bad)))
for k,a,x,y in bad: print("  %s%r\n     py=%r\n     rs=%r"%(k,a,x,y))
