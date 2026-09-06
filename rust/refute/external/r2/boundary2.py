"""Boundary lens: threading, reentrancy, input mutation, kwargs, MAX_N, arity."""
import os, sys, threading, itertools
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.abspath(os.path.join(HERE,"..","..","..",".."))
sys.path.insert(0,os.path.join(ROOT,"src"))
import fastcore, fastcore_rs
PY_F=fastcore._force_py; PY_R=fastcore._rank_py
RS_F=fastcore_rs.force;  RS_R=fastcore_rs.rank
fails=[]
def rep(tag,py,rs):
    ok = (py==rs)
    print(("  OK   " if ok else "  DIFF ")+tag+"  py=%r rs=%r"%(py,rs))
    if not ok: fails.append((tag,py,rs))
def C(fn,*a,**k):
    try:
        if fn in (PY_F,PY_R): fastcore._INV.clear()
        v=fn(*a,**k)
        if isinstance(v,tuple): return (bool(v[0]),tuple(sorted(v[1])))
        return int(v)
    except Exception as e: return type(e).__name__

print("--- kwargs / defaults ---")
rep("force kw", C(PY_F,rows=[[1,-1]],n=1,T0=set()), C(RS_F,rows=[[1,-1]],n=1,T0=set()))
rep("force kw p", C(PY_F,[[1,-1]],1,set(),p=7), C(RS_F,[[1,-1]],1,set(),p=7))
rep("rank kw", C(PY_R,rows=[[1,2]]), C(RS_R,rows=[[1,2]]))
rep("P const", fastcore.P, fastcore_rs.P)
rep("force arity3", C(PY_F,[[1,-1]],1), C(RS_F,[[1,-1]],1))
rep("force arity5", C(PY_F,[[1,-1]],1,set(),7,9), C(RS_F,[[1,-1]],1,set(),7,9))

print("--- input mutation ---")
rows=[[1,-1,0,0],[0,0,1,-1]]; rows_c=[r[:] for r in rows]; T0={0}; T0_c=set(T0)
ok,T=RS_F(rows,2,T0)
rep("rows unmutated", rows_c, rows)
rep("T0 unmutated", T0_c, T0)
rep("T0 is not result", False, T is T0)
T.add(999)
ok2,T2=RS_F(rows,2,{0})
rep("fresh set each call", (True,(0,1)), (bool(ok2),tuple(sorted(T2))))
fs=frozenset([0])
r=RS_F(rows,2,fs)
rep("frozenset T0 -> set", "set", type(r[1]).__name__)
rp=PY_F(rows,2,fs)
rep("py frozenset T0 type", type(rp[1]).__name__, type(r[1]).__name__)

print("--- MAX_N boundary ---")
N=1<<20
rep("n=2^20 T0 full-ish", C(PY_F,[],N,set(range(N))), C(RS_F,[],N,set(range(N))))
rep("n=2^20+1 T0 full",   C(PY_F,[],N+1,set(range(N+1))), C(RS_F,[],N+1,set(range(N+1))))
rep("n=2^20 rows=[] T0={}", C(PY_F,[],N,set()), C(RS_F,[],N,set()))

print("--- reentrancy: iterable that calls back into the kernel ---")
class Reenter:
    def __init__(s,data): s.data=data
    def __iter__(s):
        for x in s.data:
            RS_F([[1,-1]],1,set())      # re-enter while the outer borrow is held
            RS_R([[1,2],[3,4]])
            yield x
rep("reenter rows force", C(PY_F,list(Reenter([[1,-1,0,0],[0,0,1,-1]])),2,set()),
                          C(RS_F,Reenter([[1,-1,0,0],[0,0,1,-1]]),2,set()))
rep("reenter rows rank",  C(PY_R,list(Reenter([[1,0],[0,1]]))),
                          C(RS_R,Reenter([[1,0],[0,1]])))
class ReenterRow:
    def __init__(s,d): s.d=d
    def __iter__(s):
        for x in s.d:
            RS_R([[2,3],[4,5]],7)
            yield x
rep("reenter inner row", C(PY_R,[list(ReenterRow([1,2])),[3,4]]),
                         C(RS_R,[ReenterRow([1,2]),[3,4]]))

print("--- threads: 8 workers hammering the thread_local scratch ---")
base=[[1,-1,0,0,0,0],[0,0,1,-1,0,0],[0,0,0,0,1,-1],[1,0,0,-1,0,0],[2,1,0,0,-2,-1]]
expect=[]
for k in range(1,6):
    fastcore._INV.clear()
    o,T=PY_F(base[:k],3,set())
    expect.append((bool(o),tuple(sorted(T)),PY_R(base[:k])))
errs=[]
def worker(seed):
    import random
    rng=random.Random(seed)
    for _ in range(4000):
        k=rng.randint(1,5)
        o,T=RS_F(base[:k],3,set())
        got=(bool(o),tuple(sorted(T)),RS_R(base[:k]))
        if got!=expect[k-1]: errs.append((seed,k,got,expect[k-1]))
ths=[threading.Thread(target=worker,args=(i,)) for i in range(8)]
[t.start() for t in ths]; [t.join() for t in ths]
rep("8-thread consistency", 0, len(errs))
if errs: print("   sample:",errs[:3])

print("="*50)
print("boundary2 fails:",len(fails))
for f in fails: print("  ",f)
