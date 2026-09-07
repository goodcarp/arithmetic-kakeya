"""Does the answer of a COMPLETE sweep depend on WHICH slopes are in the pool?

The projective group fixing tau (slope -1) is sharply 2-transitive on the other
slopes, so exactly two labels can be normalised, e.g. to (1,0) and (0,1).  A
k-slope alphabet therefore carries k-2 genuine moduli.  POOL3 pins that one
modulus at slope 1; POOL4 pins two at (1,2); POOL6 pins four at (1,2,3,1/2).
Every "complete" sweep in the record is complete in the LABELLINGS and a single
point in the MODULI.  This re-runs two of those complete sweeps with the moduli
moved and asks whether the reported answer is stable.
"""
import sys, os, random
from fractions import Fraction as F
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "..", "..", "..", "src")
sys.path.insert(0, os.path.abspath(SRC))
from search import scan_dims, POOL3, POOL6
import fastcore

def run(tag, d, pool, target, max_t):
    fastcore._INV.clear()
    h, b, c, tot, el = scan_dims(d, pool, target, max_t=max_t, limit=None,
                                 tlimit=1e9, verbose=False)
    print(f"  {tag:28s} d={d} pool={pool}\n"
          f"      scanned {c}/{tot} complete={c>=tot}  best={b}  hits={len(h)}"
          f"  [{el:.1f}s]", flush=True)
    return b, len(h), c, tot

print("== n=4, d=[2,2], |T|<=1, target 7/4 : record says best 7/4 with 120 witnesses ==")
run("POOL6 (record)", [2,2], POOL6, F(7,4), 1)
rng = random.Random(20260906)
def rand_pool(k, rng):
    out = [(1,0), (0,1)]
    while len(out) < k:
        a = rng.randint(-4,4); b = rng.randint(-4,4)
        if (a,b)==(0,0) or a+b==0: continue
        g = __import__("math").gcd(abs(a),abs(b)) or 1
        s = (a//g, b//g)
        if s[0] < 0 or (s[0]==0 and s[1]<0): s = (-s[0], -s[1])
        if any(x[0]*s[1]-x[1]*s[0]==0 for x in out): continue
        out.append(s)
    return out
for i in range(3):
    run(f"random 6-slope #{i+1}", [2,2], rand_pool(6, rng), F(7,4), 1)

print()
print("== Goal-1 3-slope moduli: d=[2,3], |T|<=1, target 9/5 ==")
print("   (record: 3-slope {0,oo,1} complete over 1024 graphs, nothing below 9/5)")
for third in [(1,1),(1,2),(2,1),(1,3),(3,1),(1,-2),(1,4),(3,2)]:
    if third[0]+third[1] == 0: continue
    run(f"third slope {third}", [2,3], [(1,0),(0,1),third], F(9,5), 1)
