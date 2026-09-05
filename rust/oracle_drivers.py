"""Oracle harness for the three drivers with no cheap fixture.

Imports the REAL g2_tall / cycles8 / stacked modules from ../src and calls
their own run()/main() functions at small parameters, printing exactly what
each driver's __main__ prints.  Nothing here reimplements the search: the
Python under test is the unmodified original, so its stdout is the oracle.

usage:
  oracle_drivers.py g2-tall <rows> [max_t]
  oracle_drivers.py cycles8 <poolsize> [target p/q]
  oracle_drivers.py stacked <poolsize> [max_t]
"""
import sys, os, json
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC)
from fractions import Fraction

BIG = 10.0 ** 9   # a tlimit that never trips, so the run is deterministic

def main():
    which = sys.argv[1]
    if which == "g2-tall":
        import g2_tall
        rows_ = int(sys.argv[2])
        max_t = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        b, bo, h, el = g2_tall.run(rows_, max_t=max_t, tlimit=BIG)
        print("RESULT", json.dumps({"tag": f"g2_tall_2x{rows_}", "d": [2, rows_],
              "pool": 3, "max_t": 1, "target": "<11/6",
              "best": str(b) if b else None, "hits": len(h),
              "complete": (el < 700), "seconds": round(el, 1)}), flush=True)
    elif which == "cycles8":
        import cycles8
        from search import POOL3, POOL4, POOL5, POOL6, POOL8
        pool = {3: POOL3, 4: POOL4, 5: POOL5, 6: POOL6, 8: POOL8}[int(sys.argv[2])]
        target = Fraction(sys.argv[3]) if len(sys.argv) > 3 else Fraction(67, 40)
        b, bo, h, tested = cycles8.main(pool, target=target, tlimit=BIG)
        print("RESULT", json.dumps({"tag": "cycles8", "pool": len(pool),
              "best": str(b) if b else None, "hits": len(h), "tested": tested}), flush=True)
        for x in h[:20]:
            print("HITOBJ", json.dumps(x, default=str), flush=True)
    elif which == "stacked":
        import stacked
        from search import POOL3, POOL4, POOL5, POOL6, POOL8
        k = int(sys.argv[2])
        pool = {3: POOL3, 4: POOL4, 5: POOL5, 6: POOL6, 8: POOL8}[k]
        max_t = int(sys.argv[3]) if len(sys.argv) > 3 else 2
        b, bo, h, el = stacked.run(pool, max_t=max_t)
        print(f"POOL{k}: best score over all interfaces = {b} ({float(b) if b else None})")
        print(f"   witness: interface labels={bo[0]} m={bo[1]} r={len(bo[2])} "
              f"t={bo[4]} T0={bo[3]}")
        print(f"   strictly-better-than-7/4 hits: {len(h)}   [{el:.1f}s]")
        for x in h[:5]:
            print("      ", x)
    else:
        raise SystemExit(f"unknown driver {which}")

main()
