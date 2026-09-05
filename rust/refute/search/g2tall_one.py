"""Oracle for one g2_tall.run, printing exactly what g2_tall.py's __main__ prints.
usage: g2tall_one.py <rows> [max_t] [tlimit]"""
import sys, os, json
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src")
sys.path.insert(0, SRC)
import g2_tall
rows_ = int(sys.argv[1])
max_t = int(sys.argv[2]) if len(sys.argv) > 2 else 1
tlimit = float(sys.argv[3]) if len(sys.argv) > 3 else 700.0
b, bo, h, el = g2_tall.run(rows_, max_t=max_t, tlimit=tlimit)
print("RESULT", json.dumps({"tag": f"g2_tall_2x{rows_}", "d": [2, rows_],
      "pool": 3, "max_t": 1, "target": "<11/6",
      "best": str(b) if b else None, "hits": len(h),
      "complete": (el < 700), "seconds": round(el, 1)}), flush=True)
