"""The two Katz-Tao iteration ladders, in exact arithmetic.

Corollary 3.5 (vertical line segments), Katz-Tao 'New bounds for Kakeya
problems' (arXiv:math/0102135):
        SD(beta)  ==>  SD( (4 beta - 1) / (2 beta) )
Theorem 4.1 (corners), same paper:
        SD(beta)  ==>  SD( (3 beta^2 + 2 beta - 2) / (beta^2 + 3 beta - 2) )

On the object side beta = (m+|R|)/(n-|T|) = p/q, so the maps on (p,q) are
        segments:  (p, q) -> (4p - q, 2p)
        corners :  (p, q) -> (3p^2 + 2pq - 2q^2,  p^2 + 3pq - 2q^2)
q is the number of vertices that must be forced, p the number of edges plus
recorded projections.  Both ladders start at the trivial object (p,q) = (2,1).
"""
from fractions import Fraction
import sympy as sp


def seg(p, q):
    return 4 * p - q, 2 * p


def cor(p, q):
    return 3 * p * p + 2 * p * q - 2 * q * q, p * p + 3 * p * q - 2 * q * q


def norm(p, q):
    g = sp.igcd(p, q)
    return p // g, q // g


def ladder(step, depth=6):
    p, q = 2, 1
    out = [(p, q)]
    for _ in range(depth):
        p, q = norm(*step(p, q))
        out.append((p, q))
    return out


if __name__ == "__main__":
    x = sp.symbols('x')
    print("segment ladder  (fixed point 1 + sqrt2/2):")
    for p, q in ladder(seg, 8):
        print(f"   (m+|R|, n-|T|) = ({p:>10}, {q:>10})   score = {Fraction(p,q)} "
              f"= {p/q:.9f}")
    print("   fixed point:", sp.nsimplify(sp.solve(sp.Eq(x, (4*x-1)/(2*x)), x)[-1]),
          "=", float(max(sp.solve(sp.Eq(x, (4*x-1)/(2*x)), x))))
    print()
    print("corner ladder   (fixed point = largest root of x^3 - 4x + 2):")
    for p, q in ladder(cor, 4):
        print(f"   (m+|R|, n-|T|) = ({p:>10}, {q:>10})   score = {Fraction(p,q)} "
              f"= {p/q:.9f}")
    fp = sp.solve(sp.Eq(x, (3*x**2+2*x-2)/(x**2+3*x-2)), x)
    print("   fixed-point equation:",
          sp.simplify(sp.expand(x*(x**2+3*x-2) - (3*x**2+2*x-2))), "= 0")
    roots = sp.Poly(x**3 - 4*x + 2, x).all_roots()
    g = max(float(r) for r in roots)
    print(f"   gamma = {g:.10f}")
    print(f"   Epoch target 1.675 < gamma ?  {1.675 < g}   "
          f"(gap = {g - 1.675:.3e})")
