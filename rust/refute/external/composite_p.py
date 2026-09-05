"""Composite / small p sweep: the Fermat 'inverse' is arithmetic garbage for
composite p and must be reproduced bit-for-bit."""
import sys, random, itertools
sys.path.insert(0, "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src")
import fastcore, fastcore_rs
PY_F, RS_F = fastcore._force_py, fastcore_rs.force
PY_R, RS_R = fastcore._rank_py, fastcore_rs.rank
def call(fn,*a):
    try: return ("ok", fn(*a))
    except BaseException as e: return ("raise", type(e).__name__)
bad=[]; n=0
rnd = random.Random(7)
for p in list(range(1,41)) + [255,256,257,1024,65535,65536,65537,4294967295,4294967291,2147483647,2147483646]:
    for it in range(400):
        nn = rnd.randrange(1,5); m = rnd.randrange(0,6)
        rows = [[rnd.randrange(-10,11) for _ in range(2*nn)] for _ in range(m)]
        T0 = set(rnd.sample(range(nn), rnd.randrange(0,nn+1)))
        fastcore._INV.clear(); a = call(PY_F,[r[:] for r in rows],nn,set(T0),p)
        fastcore._INV.clear(); b = call(RS_F,[r[:] for r in rows],nn,set(T0),p)
        if a[0]=="ok": a=("ok",bool(a[1][0]),frozenset(a[1][1]))
        if b[0]=="ok": b=("ok",bool(b[1][0]),frozenset(b[1][1]))
        n+=1
        if a!=b: bad.append(("force",rows,nn,sorted(T0),p,a,b))
        fastcore._INV.clear(); a = call(PY_R,[r[:] for r in rows],p)
        fastcore._INV.clear(); b = call(RS_R,[r[:] for r in rows],p)
        n+=1
        if a!=b: bad.append(("rank",rows,None,None,p,a,b))
print("composite/small p sweep: checks=%d mismatches=%d" % (n,len(bad)))
seen=set()
for b in bad:
    k=(b[0],b[4])
    if k in seen: continue
    seen.add(k); print("  ",b)

# --- misc boundary args ----------------------------------------------------
def show(tag, f, *a, **k):
    fastcore._INV.clear(); x = call(lambda: f(*a,**k))
    print(tag, x)
for tag, fn in (("py", PY_F), ("rs", RS_F)):
    fastcore._INV.clear()
    try: r = fn([[1,-1,0,0]], 1<<70, set())
    except BaseException as e: r = (type(e).__name__, str(e)[:60])
    print("n=2**70  %s: %r" % (tag, r))
for tag, fn in (("py", PY_R), ("rs", RS_R)):
    fastcore._INV.clear()
    try: r = fn([[1,0],[0,1]], 1<<70)
    except BaseException as e: r = (type(e).__name__, str(e)[:60])
    print("p=2**70  %s: %r" % (tag, r))
for tag, fn in (("py", PY_R), ("rs", RS_R)):
    fastcore._INV.clear()
    try: r = fn([[1,0],[0,1]], p=7)
    except BaseException as e: r = (type(e).__name__, str(e)[:60])
    print("p kwarg  %s: %r" % (tag, r))
for tag, fn in (("py", PY_F), ("rs", RS_F)):
    fastcore._INV.clear()
    try: r = fn({(1,0,0,0):1, (0,1,0,0):1}, 2, set())
    except BaseException as e: r = (type(e).__name__, str(e)[:60])
    print("rows=dict %s: %r" % (tag, r))
for tag, fn in (("py", PY_R), ("rs", RS_R)):
    fastcore._INV.clear()
    try: r = fn({(1,0):1, (0,1):1})
    except BaseException as e: r = (type(e).__name__, str(e)[:60])
    print("rank rows=dict %s: %r" % (tag, r))
