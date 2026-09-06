"""g2_tall.run with a settable tlimit, printing the driver's own RESULT block.
usage: g2tall_tl.py <rows> <max_t> <tlimit>"""
import sys, json
sys.path.insert(0, "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src")
import g2_tall
rows_ = int(sys.argv[1]); max_t = int(sys.argv[2]); tl = float(sys.argv[3])
b, bo, h, el = g2_tall.run(rows_, max_t=max_t, tlimit=tl)
print("RESULT", json.dumps({"tag": f"g2_tall_2x{rows_}", "d": [2, rows_],
      "pool": 3, "max_t": 1, "target": "<11/6",
      "best": str(b) if b else None, "hits": len(h),
      "complete": (el < 700), "seconds": round(el, 1)}), flush=True)
