"""One scan job.  usage: scan1.py <tag> <d, e.g. 2x3> <poolsize> <maxt> <target p/q> [limit] [tlimit]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
from fractions import Fraction
from search import scan_dims, POOL3, POOL4, POOL5, POOL6, POOL8

tag = sys.argv[1]
d = [int(x) for x in sys.argv[2].split("x")]
pool = {3: POOL3, 4: POOL4, 5: POOL5, 6: POOL6, 8: POOL8}[int(sys.argv[3])]
maxt = int(sys.argv[4])
target = Fraction(sys.argv[5])
limit = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6] != "-" else None
tlimit = float(sys.argv[7]) if len(sys.argv) > 7 else 3000.0

h, b, c, tot, el = scan_dims(d, pool, target, max_t=maxt, limit=limit, seed=11,
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
