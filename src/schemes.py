"""Route B: the exponent map of a single-level Katz-Tao scheme, and its fixed point.

Anatomy of Corollary 3.5 (`New bounds for Kakeya problems`, math/0102135),
stripped to its counting skeleton.  A scheme is given by four exponents:

  c  number of copies of G in the gadget          (pairs: 2)
  e  number of gluing constraints in the gadget   (pairs: 1)
       -> Cauchy-Schwarz lower bound   #Gadget >= #G^c / N^e
  u  fibre bound exponent, #fibre <= N^u          (pairs: 1)
  w  popularity exponent, N* = #fibre / (#Gadget / N^w)   (pairs: 2)

Chaining them:
  SD(beta) on the fibre :  #fibre <~ (N*)^beta = (#fibre N^w / #Gadget)^beta
     =>  #fibre >~ (#Gadget / N^w)^{beta/(beta-1)}
  with #fibre <= N^u :     #Gadget <~ N^{w + u (beta-1)/beta}
  with the C-S bound  :    #G <~ N^{(e + w + u(beta-1)/beta)/c}

so the scheme's exponent map is

       g(beta) = ( e + w + u (beta - 1)/beta ) / c

and its fixed point solves    c beta^2 - (e + w + u) beta + u = 0.

Check: pairs (c,e,u,w) = (2,1,1,2) gives g(beta) = (4 beta - 1)/(2 beta) and
2 beta^2 - 4 beta + 1 = 0, i.e. beta = 1 + sqrt(2)/2.  Exactly Corollary 3.5.

The corner scheme (Theorem 4.1) is NOT of this form: it feeds the output of the
pair scheme back in as a bound on #([v]_nu), so its map is a ratio of quadratics
and its fixed point is a cubic.  Two-level schemes are the next enumeration.
"""
import sympy as sp
from fractions import Fraction

b = sp.symbols('b', positive=True)


def g_map(c, e, u, w):
    return sp.simplify((e + w + u * (b - 1) / b) / c)


def fixed_point(c, e, u, w):
    sols = sp.solve(sp.Eq(c * b**2 - (e + w + u) * b + u, 0), b)
    real = [sp.nsimplify(s) for s in sols if sp.im(sp.N(s)) == 0]
    return max(real, key=lambda s: float(sp.N(s))) if real else None


if __name__ == "__main__":
    print("known scheme, pairs (Cor 3.5): c,e,u,w = 2,1,1,2")
    print("   g(beta) =", g_map(2, 1, 1, 2))
    fp = fixed_point(2, 1, 1, 2)
    print("   fixed point =", fp, "=", float(sp.N(fp)))
    print()
    print("sweep of single-level schemes with fixed point in [1.5, 1.7]:")
    rows = []
    for c in range(2, 7):
        for e in range(1, 13):
            for u in range(1, 7):
                for w in range(1, 9):
                    disc = (e + u + w)**2 - 4 * c * u
                    if disc < 0:
                        continue
                    fp = ((e + u + w) + disc**0.5) / (2 * c)
                    if 1.5 <= fp <= 1.70:
                        rows.append((round(fp, 6), c, e, u, w))
    rows.sort()
    for r in rows[:25]:
        print(f"   fixed point {r[0]:.6f}   (c,e,u,w) = {r[1:]}")
    print(f"   ... {len(rows)} parameter tuples land in [1.5, 1.70]")
    print()
    print("The map depends only on (c, u, e+w), so the real parameter is that triple.")
    print()
    print("consistency check -- the naive single-level analysis of the CORNER gadget")
    print("(c,e,u,w) = (3,2,1,2) gives 3b^2 - 5b + 1 = 0:")
    fp = ((2+1+2) + ((2+1+2)**2 - 4*3*1)**0.5) / 6
    print(f"   fixed point {fp:.6f}  -- BELOW 3/2, hence not realisable.")
    print("   That is exactly why Katz-Tao could not use corners at one level and had")
    print("   to feed the pair result back in, producing a cubic instead.")
    print()
    print("Reminder: (c,e,u,w) is a *counting skeleton*, not yet a configuration.")
    print("The open half of Route B is which tuples are realisable; the 3/2 barrier")
    print("says everything below 1.5 is not.")
