"""Oracle for one rzero.sweep job, printing exactly what rzero.py's __main__ prints.
usage: rzero_one.py <d e.g. 2x2> <poolsize> [limit|-] [seed] [tlimit]"""
import sys, os, json
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src")
sys.path.insert(0, SRC)
import rzero
from search import POOL3, POOL4, POOL5, POOL6, POOL8

d = [int(x) for x in sys.argv[1].split("x")]
pool = {3: POOL3, 4: POOL4, 5: POOL5, 6: POOL6, 8: POOL8}[int(sys.argv[2])]
lim = None if len(sys.argv) <= 3 or sys.argv[3] == "-" else int(sys.argv[3])
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 0
tlimit = float(sys.argv[5]) if len(sys.argv) > 5 else 1e9

b, c, tot, fo, el = rzero.sweep(d, pool, limit=lim, seed=seed, tlimit=tlimit)
print("RESULT", json.dumps({"tag": "rzero", "d": d, "pool": len(pool),
      "scanned": c, "total": tot, "forcing_objects": fo,
      "best_score": str(b) if b else None,
      "complete": lim is None and c >= tot, "seconds": round(el, 1)}), flush=True)
