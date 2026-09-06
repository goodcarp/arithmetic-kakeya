"""Thin oracle: stacked.run(pool, max_t, target) with the driver's own print block.
usage: stacked_one.py <poolsize> <max_t> <target p/q>
"""
import sys, os
SRC = "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src"
sys.path.insert(0, SRC)
from fractions import Fraction
import stacked
from search import POOL3, POOL4, POOL5, POOL6, POOL8
k = int(sys.argv[1]); max_t = int(sys.argv[2]); target = Fraction(sys.argv[3])
pool = {3: POOL3, 4: POOL4, 5: POOL5, 6: POOL6, 8: POOL8}[k]
b, bo, h, el = stacked.run(pool, max_t=max_t, target=target)
print(f"POOL{k}: best score over all interfaces = {b} ({float(b) if b else None})")
print(f"   witness: interface labels={bo[0]} m={bo[1]} r={len(bo[2])} "
      f"t={bo[4]} T0={bo[3]}")
print(f"   strictly-better-than-7/4 hits: {len(h)}   [{el:.1f}s]")
for x in h[:5]:
    print("      ", x)
