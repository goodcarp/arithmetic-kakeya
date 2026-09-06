"""Measure the pure-Python cycles8 rate: run cycles8.main under a short tlimit
and report how many pairs it tested.  usage: rate_c8.py <pool> <tlimit_seconds>"""
import sys, os, time, json
K = "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya"
sys.path.insert(0, os.path.join(K, "src"))
from fractions import Fraction
import cycles8
from search import POOL3, POOL4, POOL6
pools = {3: POOL3, 4: POOL4, 6: POOL6}
pool = pools[int(sys.argv[1])]; tl = float(sys.argv[2])
import fastcore
print("kernel:", "PURE-PYTHON" if os.environ.get("KAKEYA_PURE_PY") else "default(PyO3 if built)",
      "| force is", getattr(fastcore.force, "__module__", "?"), flush=True)
t0 = time.time()
b, bo, h, tested = cycles8.main(pool, target=Fraction(67, 40), tlimit=tl)
el = time.time() - t0
print(json.dumps({"pool": len(pool), "tlimit": tl, "tested": tested,
                  "seconds": round(el, 1), "rate_pairs_per_s": round(tested / el, 3),
                  "hits": len(h)}), flush=True)
