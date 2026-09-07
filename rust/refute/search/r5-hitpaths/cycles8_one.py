"""Thin oracle: cycles8.main(pool, target, deg) with the driver's own print block
(copied from oracle_drivers.py's cycles8 branch).  `deg` is the only constant
made settable, and cycles8.main already takes it as a parameter -- there is no
other reference to it anywhere in cycles8.py (grep: `deg` occurs only in the
signature and in the two lines that use it).  tlimit is left at the driver's
BIG so the run is deterministic.
usage: cycles8_one.py <poolsize> <target p/q> <deg>
"""
import sys, os, json
SRC = "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src"
sys.path.insert(0, SRC)
from fractions import Fraction
import cycles8
from search import POOL3, POOL4, POOL5, POOL6, POOL8
BIG = 10.0 ** 9
k = int(sys.argv[1]); target = Fraction(sys.argv[2]); deg = int(sys.argv[3])
pool = {3: POOL3, 4: POOL4, 5: POOL5, 6: POOL6, 8: POOL8}[k]
b, bo, h, tested = cycles8.main(pool, target=target, deg=deg, tlimit=BIG)
print("RESULT", json.dumps({"tag": "cycles8", "pool": len(pool),
      "best": str(b) if b else None, "hits": len(h), "tested": tested}), flush=True)
for x in h[:20]:
    print("HITOBJ", json.dumps(x, default=str), flush=True)
