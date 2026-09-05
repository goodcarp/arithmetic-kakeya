"""Concurrency: the Rust keeps its scratch in a thread_local and releases the
GIL with py.detach() while it computes.  If that scratch ever leaked between
threads, answers would depend on interleaving.  Run identical and mixed
workloads from N threads and demand the single-threaded answers."""
import random
import sys
import threading

sys.path.insert(0, ".")
import harness

mod = harness.load_rs(sys.argv[1] if len(sys.argv) > 1 else "shipped")
P = (1 << 31) - 1
MODULI = [1, 2, 3, 7, 91, 65537, P, 2147483648, 4294967295]

rng = random.Random(99)
work = []
for _ in range(400):
    p = rng.choice(MODULI)
    w = rng.choice([2, 4, 6, 8])
    rows = [[rng.randint(-3, 3) if rng.random() < .6 else rng.randrange(max(p, 2))
             for _ in range(w)] for _ in range(rng.randint(1, 6))]
    if rng.random() < .5:
        work.append(("rank", (rows,), {"p": p}))
    else:
        work.append(("force", (rows, w // 2, set()), {"p": p}))

# single-threaded reference answers from the Rust itself, plus Python
gold = []
for k, a, kw in work:
    harness.INV.clear()
    py = (harness.PY_FORCE if k == "force" else harness.PY_RANK)(*a, **kw)
    rs = getattr(mod, k)(*a, **kw)
    py = (bool(py[0]), tuple(sorted(py[1]))) if k == "force" else py
    rs = (bool(rs[0]), tuple(sorted(rs[1]))) if k == "force" else rs
    assert py == rs, (k, a, kw, py, rs)
    gold.append(rs)

bad = []
lock = threading.Lock()


def worker(shift):
    for rep in range(20):
        for i in range(len(work)):
            j = (i + shift * 37) % len(work)
            k, a, kw = work[j]
            v = getattr(mod, k)(*a, **kw)
            v = (bool(v[0]), tuple(sorted(v[1]))) if k == "force" else v
            if v != gold[j]:
                with lock:
                    bad.append((shift, rep, j, gold[j], v))


ts = [threading.Thread(target=worker, args=(t,)) for t in range(8)]
for t in ts:
    t.start()
for t in ts:
    t.join()
print(f"threads=8 reps=20 items={len(work)} "
      f"calls={8*20*len(work)} mismatches={len(bad)}")
for b in bad[:10]:
    print("  ", b)
