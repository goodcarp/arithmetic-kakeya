import sys, threading, random
sys.path.insert(0, "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src")
import fastcore, fastcore_rs
PY_F, RS_F = fastcore._force_py, fastcore.force
PY_R, RS_R = fastcore._rank_py, fastcore.rank
print("kernel module:", fastcore.force.__module__)

ROWS = [[1,-1,0,0,0,0],[0,0,1,-1,0,0],[0,0,0,0,1,-1]]

# 1. re-entrant rows iterable: iterating it calls force again
class Reenter:
    def __iter__(self):
        for r in ROWS:
            fastcore_rs.force([[1,-1,0,0],[0,0,1,-1]], 2, set())
            fastcore_rs.rank([[1,2],[3,4]])
            yield r
fastcore._INV.clear(); a = PY_F(list(Reenter()), 3, set())
b = fastcore_rs.force(Reenter(), 3, set())
print("reentrant rows: py=%r rs=%r  %s" % (a, b, "SAME" if (bool(a[0]),frozenset(a[1]))==(bool(b[0]),frozenset(b[1])) else "DIFF"))

# 2. re-entrant T0
class ReenterT0:
    def __iter__(self):
        fastcore_rs.rank([[1,0],[0,1]])
        yield 0
fastcore._INV.clear(); a = PY_F(ROWS, 3, set(ReenterT0()))
b = fastcore_rs.force(ROWS, 3, ReenterT0())
print("reentrant T0:   py=%r rs=%r  %s" % (a, b, "SAME" if (bool(a[0]),frozenset(a[1]))==(bool(b[0]),frozenset(b[1])) else "DIFF"))

# 3. row that is itself a generator
b = fastcore_rs.rank([(x for x in [1,0]), (x for x in [0,1])])
fastcore._INV.clear(); a = PY_R([[1,0],[0,1]])
print("generator rows inner: py=%r rs=%r %s" % (a,b,"SAME" if a==b else "DIFF"))

# 4. concurrent threads hammering the shared thread_local buffers
errs = []
def worker(seed):
    rnd = random.Random(seed)
    for _ in range(3000):
        n = rnd.randrange(1,6); m = rnd.randrange(0,7)
        rows = [[rnd.randrange(-3,4) for _ in range(2*n)] for _ in range(m)]
        T0 = set(rnd.sample(range(n), rnd.randrange(0,n+1)))
        r1 = fastcore_rs.force(rows, n, T0)
        r2 = fastcore_rs.rank(rows)
        with LOCK:
            fastcore._INV.clear(); e1 = PY_F([r[:] for r in rows], n, set(T0))
            fastcore._INV.clear(); e2 = PY_R([r[:] for r in rows])
        if (bool(e1[0]),frozenset(e1[1])) != (bool(r1[0]),frozenset(r1[1])) or e2 != r2:
            errs.append((rows,n,sorted(T0),e1,r1,e2,r2))
LOCK = threading.Lock()
ths = [threading.Thread(target=worker, args=(i,)) for i in range(6)]
for t in ths: t.start()
for t in ths: t.join()
print("threaded 6x3000: mismatches=%d" % len(errs))
for e in errs[:5]: print("  ", e)

# 5. T0 not aliased / not mutated, result is fresh each call
s = {0}
ok1, T1 = fastcore_rs.force(ROWS, 3, s)
ok2, T2 = fastcore_rs.force(ROWS, 3, s)
print("aliasing: T0=%r T1 is s=%r T1 is T2=%r T1==T2=%r types=%r/%r" %
      (s, T1 is s, T1 is T2, T1 == T2, type(ok1).__name__, type(T1).__name__))
T1.add(99)
ok3, T3 = fastcore_rs.force(ROWS, 3, s)
print("after mutating returned set: %r  (s still %r)" % (T3, s))
