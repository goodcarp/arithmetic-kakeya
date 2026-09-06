"""Test every antigravity-cli candidate, plus a systematic p=0 error-ordering sweep."""
import itertools, os, sys
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.abspath(os.path.join(HERE,"..","..","..",".."))
sys.path.insert(0,os.path.join(ROOT,"src"))
import fastcore, fastcore_rs
PY_F=fastcore._force_py; PY_R=fastcore._rank_py
RS_F=fastcore_rs.force;  RS_R=fastcore_rs.rank
def cp(fn,*a,**k):
    fastcore._INV.clear()
    try:
        v=fn(*a,**k)
        return (bool(v[0]),tuple(sorted(v[1]))) if isinstance(v,tuple) else int(v)
    except Exception as e: return type(e).__name__
def cr(fn,*a,**k):
    try:
        v=fn(*a,**k)
        return (bool(v[0]),tuple(sorted(v[1]))) if isinstance(v,tuple) else int(v)
    except Exception as e: return type(e).__name__

CLAIMS=[
 ("A1", "rank",  ([[], [1]],), {"p":0}),
 ("A2", "force", ([], 1, []), {"p":0}),
 ("A3", "force", ([[0,0]], 2, [0]), {"p":0}),
 ("A4", "force", ([[0,0,0]], 2, [0]), {"p":0}),
 ("A5", "rank",  ([[0,1],[1,0,0],[1,1,0]],), {"p":5}),
 ("A6", "rank",  ([[1,2,3],[1,2],[1]],), {"p":5}),
 ("A7", "force", ([[1]], 0, []), {"p":5}),
 ("A8", "force", ([[1]], -1, [-1]), {"p":5}),
 ("A9", "force", ([], 2, [-5,10]), {"p":5}),
 ("A10","force", ([[1,4,0,0]], 2, [-1]), {"p":5}),
 ("A11","force", ([], 2, [1,1,1]), {"p":5}),
 ("A12","rank",  ([[1,2],[3,4]],), {"p":1}),
 ("A13","force", ([[1,2]], 1, []), {"p":1}),
 ("A14","force", ([[0,0,1,2]], 2, [1]), {"p":5}),
 ("A15","rank",  ([[2,1],[0,2]],), {"p":4}),
 # my own p=0 ordering probes
 ("M1", "rank",  ([[1],[]],), {"p":0}),
 ("M2", "rank",  ([[],[]],), {"p":0}),
 ("M3", "rank",  ([[]],), {"p":0}),
 ("M4", "rank",  ([],), {"p":0}),
 ("M5", "force", ([[1,-1]], 1, [0]), {"p":0}),
 ("M6", "force", ([[1,-1]], 1, []), {"p":0}),
 ("M7", "force", ([[1]], 1, []), {"p":0}),
 ("M8", "force", ([[],[1,-1]], 1, []), {"p":0}),
 ("M9", "force", ([[1,-1,1]], 2, [0]), {"p":0}),
 ("M10","force", ([[1,-1,1,1]], 2, [0]), {"p":0}),
 ("M11","force", ([[0,0,0,0],[1]], 2, []), {"p":0}),
 ("M12","force", ([[0,0,0,0],[1]], 2, []), {"p":7}),
 ("M13","rank",  ([[0,2],[1]],), {"p":7}),
 ("M14","rank",  ([[1],[2,3]],), {"p":7}),
 ("M15","rank",  ([[1,2,3],[4,5]],), {"p":7}),
 ("M16","rank",  ([[],[1,2]],), {"p":7}),
 ("M17","force", ([[1,-1]], 2, [1]), {"p":7}),
]
bad=[]
for tag,kind,args,kw in CLAIMS:
    f_py,f_rs=(PY_F,RS_F) if kind=="force" else (PY_R,RS_R)
    a=cp(f_py,*args,**kw); b=cr(f_rs,*args,**kw)
    m = "OK  " if a==b else "DIFF"
    print("%s %-4s %s%r p=%s  py=%r  rs=%r"%(m,tag,kind,args,kw.get("p"),a,b))
    if a!=b: bad.append(tag)

print("\n--- systematic p=0 / p=1 / p=2 error-ordering sweep ---")
R=[]
for L in range(5):
    for t in itertools.product([0,1],repeat=L): R.append(list(t))
cases=0; sweepbad=[]
for p in (0,1,2):
    for r1 in R:
        for r2 in R:
            for rows in ([r1],[r1,r2]):
                cases+=1
                a=cp(PY_R,rows,p); b=cr(RS_R,rows,p)
                if a!=b and len(sweepbad)<20: sweepbad.append(("rank",list(rows),p,a,b))
                for n in (0,1,2,3):
                    for T0 in (set(),{0},{1},{-1,0}):
                        cases+=1
                        a=cp(PY_F,rows,n,T0,p); b=cr(RS_F,rows,n,T0,p)
                        if a!=b and len(sweepbad)<20: sweepbad.append(("force",list(rows),n,sorted(T0),p,a,b))
print("sweep cases %d  mismatches %d"%(cases,len(sweepbad)))
for s in sweepbad: print("   ",s)
print("\nclaim diffs:",bad)
