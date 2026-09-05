import sys, time
sys.path.insert(0, ".")
import harness, cases_hand

variant = sys.argv[1] if len(sys.argv) > 1 else "shipped"
mod = harness.load_rs(variant)
r = harness.Runner(mod, variant + "/hand")
C = cases_hand.cases()
print("cases:", len(C), flush=True)
t0 = time.time()
for i, (kind, args, kwargs) in enumerate(C):
    t = time.time()
    r.check(kind, *args, **kwargs)
    dt = time.time() - t
    if dt > 1.0:
        print(f"  SLOW #{i} {dt:.1f}s {kind} p={kwargs.get('p')}", flush=True)
    if i % 200 == 0:
        print(f"  .. {i}/{len(C)} {time.time()-t0:.1f}s", flush=True)
sys.exit(1 if r.report() else 0)
