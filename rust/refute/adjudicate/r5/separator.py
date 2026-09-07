# Adjudication r5 / finding 4: does the matching-suffix reading vs the permissive
# reading actually SEPARATE?  i.e. is there an object with identical (m, |R|, n, |T|)
# -- hence identical score -- that is INVALID (not fully forced) under matching-suffix
# but VALID under permissive?  If yes, a 0-hit sweep under matching-suffix does not
# transfer to the permissive reading.
import sys, os, itertools, random
sys.path.insert(0, os.path.expanduser(
    "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src"))
from fractions import Fraction
from kakeya import score, ConstructibleGraph

X = [(0,0), (1,0), (0,1), (1,1)]        # (0,0)=zero label; a+b != 0 for the rest
NZ = [x for x in X if x != (0,0)]

d = [2, 2]
verts = list(itertools.product(range(1,3), range(1,3)))
# bundles: f_1 keys = (1,)   ; f_2 keys = (a1, 1) for a1 in 1..2
k1 = [(1,)]
k2 = [(1,1), (2,1)]

random.seed(20260906)
found = []
tried = 0
for lab1 in X:
  for lab21 in X:
    for lab22 in X:
      f = [ {(1,): lab1}, {(1,1): lab21, (2,1): lab22} ]
      for rsize in (0,1):
        for R in itertools.combinations([(v,x) for v in verts for x in NZ], rsize):
          for tsize in (1,2):
            for T in itertools.combinations(verts, tsize):
              tried += 1
              a = score(X, d, f, list(T), list(R), backend="exact", permissive=False)
              b = score(X, d, f, list(T), list(R), backend="exact", permissive=True)
              if a.get("errors"): continue
              assert a["m"] == b["m"] and a["r"] == b["r"] and a["n"] == b["n"] and a["t"] == b["t"], (a,b)
              if (not a["ok"]) and b["ok"]:
                found.append((f, list(T), list(R), b["score"]))
print("configurations tried:", tried)
print("separating (invalid matching-suffix, VALID permissive, same score):", len(found))
for item in found[:5]:
    print("  f=", item[0], " T=", item[1], " R=", item[2], " score=", item[3])
if found:
    best = min(found, key=lambda z: z[3])
    print("best separating score:", best[3], "=", float(best[3]))
