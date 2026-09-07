"""Oracle: scan1.py with `seed` taken from the command line instead of the
literal 11.  `seed` is a real parameter of search.scan_dims (default 0); it
occurs in exactly ONE place inside scan_dims (`rng = random.Random(seed)`),
so passing it through is not a shim-constant edit.  Everything else --
including the RESULT/HITOBJ rendering -- is copied verbatim from scan1.py.
usage: scan_seed.py <tag> <d> <poolsize> <maxt> <target> <limit|-> <tlimit> <seed>
"""
import sys, os, json
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "src")
sys.path.insert(0, SRC)
from fractions import Fraction
from search import scan_dims, POOL3, POOL4, POOL5, POOL6, POOL8

tag = sys.argv[1]
d = [int(x) for x in sys.argv[2].split("x")]
pool = {3: POOL3, 4: POOL4, 5: POOL5, 6: POOL6, 8: POOL8}[int(sys.argv[3])]
maxt = int(sys.argv[4])
target = Fraction(sys.argv[5])
limit = int(sys.argv[6]) if sys.argv[6] != "-" else None
tlimit = float(sys.argv[7])
seed = int(sys.argv[8])

h, b, c, tot, el = scan_dims(d, pool, target, max_t=maxt, limit=limit, seed=seed,
                             tlimit=tlimit, verbose=True)
print("RESULT", json.dumps({"tag": tag, "d": d, "pool": len(pool), "max_t": maxt,
      "target": str(target), "scanned": c, "total": tot,
      "best": str(b) if b else None, "hits": len(h),
      "complete": (limit is None and c >= tot), "seconds": round(el, 1)}), flush=True)
for hh in h:
    print("HITOBJ", json.dumps({k: (str(v) if k == "score" else
           ([list(x) for x in v] if k == "labels" else
            [[g[0], list(g[1])] for g in v] if k == "gens" else v))
           for k, v in hh.items()}), flush=True)
