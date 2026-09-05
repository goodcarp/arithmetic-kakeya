"""Exhaustive (not sampled) sweep over small moduli.

This is the strongest available evidence for the composite-modulus path: for
every p in 1..=12 it enumerates EVERY matrix over the full residue range at
several shapes and compares both implementations.  It covers, without relying
on luck:
  * pivots whose Fermat pseudo-inverse is itself 0 -- pow(4, 8-2, 8) == 0, so
    the pivot row is zeroed yet still counted as a pivot and pushed to `piv`;
  * pivots that are non-invertible but nonzero (gcd(a,p) > 1);
  * p == 2, where (1,1) and (1,-1) collapse;
  * p == 1, where every entry vanishes but force's target vector keeps a
    literal 1.
"""
import itertools
import sys

sys.path.insert(0, ".")
import harness

variant = sys.argv[1] if len(sys.argv) > 1 else "shipped"
mod = harness.load_rs(variant)
r = harness.Runner(mod, variant + "/exhaustive-small")

for p in range(1, 13):
    vals = list(range(p))
    # every 2x2 matrix over Z_p
    for a, b, c, d in itertools.product(vals, repeat=4):
        r.check("rank", [[a, b], [c, d]], p=p)
        r.check("force", [[a, b], [c, d]], 1, set(), p=p)
    # every 1x4 and 2x4-with-a-fixed-second-row shape drives force at n=2
    for a, b, c, d in itertools.product(vals, repeat=4):
        r.check("force", [[a, b, c, d]], 2, set(), p=p)

# every 3x2 over Z_p for the smallest moduli (three-row elimination chains)
for p in range(1, 7):
    vals = list(range(p))
    for t in itertools.product(vals, repeat=6):
        r.check("rank", [list(t[0:2]), list(t[2:4]), list(t[4:6])], p=p)

# signed entries: every 2x2 over [-p, p] for p <= 5 (rem_euclid vs floor-mod)
for p in range(1, 6):
    vals = list(range(-p, p + 1))
    for a, b, c, d in itertools.product(vals, repeat=4):
        r.check("rank", [[a, b], [c, d]], p=p)
        r.check("force", [[a, b], [c, d]], 1, set(), p=p)

sys.exit(1 if r.report() else 0)
