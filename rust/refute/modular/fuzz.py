"""50k-case random differential fuzz, biased at integer arithmetic.

Strategy: pick a modulus from a list that covers 1, 2, 3, small composites,
primes and composites just under 2^32, then pick entries from a distribution
that concentrates on the boundaries where a Rust port would break -- multiples
of p, p +/- 1, values near +/- 2^63, and bools -- rather than on generic
random ints.  Shapes include ragged rows and matrices wide/tall enough to make
the RREF take several pivots, so a bad Fermat inverse propagates.
"""
import random
import sys

sys.path.insert(0, ".")
import harness

P = (1 << 31) - 1
I64MAX = (1 << 63) - 1
I64MIN = -(1 << 63)

# Only moduli the Rust accepts (1 <= p < 2^32): p<=0 and p>=2^32 are the
# contract's sanctioned ValueError divergences and would drown the signal.
MODULI = [1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 15, 91, 100, 121, 128, 255, 256, 257,
          1009, 65521, 65535, 65536, 65537,
          2147483629, P, 2147483648, 2147483649, 2147483659,
          3000000021, 4000000007, 4294967279, 4294967291,
          4294967293, 4294967294, 4294967295]


def entry(rng, p):
    """Draw one row entry, heavily weighted onto arithmetic boundaries."""
    k = rng.random()
    if k < 0.34:                      # the production range
        return rng.randint(-3, 3)
    if k < 0.44:                      # exact multiples of p -> must vanish
        return p * rng.randint(-4, 4)
    if k < 0.56:                      # p +/- small: sign of the reduction
        return p * rng.randint(-3, 3) + rng.randint(-3, 3)
    if k < 0.64:                      # anywhere in [0, p)
        return rng.randrange(p) if p > 1 else 0
    if k < 0.72:                      # negative half
        return -rng.randrange(p) if p > 1 else 0
    if k < 0.80:                      # near the i64 rails
        base = rng.choice([I64MAX, I64MIN, I64MAX - 1, I64MIN + 1,
                           1 << 62, -(1 << 62), 1 << 32, -(1 << 32),
                           1 << 31, -(1 << 31)])
        return base + rng.randint(-2, 2) if abs(base) < I64MAX - 2 else base
    if k < 0.86:                      # products that would overflow a naive u64
        return rng.randrange(max(p - 1, 1)) if p > 1 else 0
    if k < 0.92:
        return rng.choice([True, False])
    return rng.randint(-(1 << 20), 1 << 20)


def make_rows(rng, p, ragged):
    nrows = rng.randint(0, 7)
    w = rng.choice([2, 2, 4, 4, 6, 8, 10])
    rows = []
    for _ in range(nrows):
        ww = w
        if ragged and rng.random() < 0.3:
            ww = max(0, w + rng.randint(-2, 2))
        rows.append([entry(rng, p) for _ in range(ww)])
    if rng.random() < 0.15 and rows:
        rows.append(list(rows[rng.randrange(len(rows))]))   # duplicate row
    if rng.random() < 0.1:
        rows = tuple(tuple(r) for r in rows)
    return rows


def run(mod, label, count, seed):
    rng = random.Random(seed)
    r = harness.Runner(mod, label)
    for _ in range(count):
        p = rng.choice(MODULI)
        ragged = rng.random() < 0.12
        rows = make_rows(rng, p, ragged)
        if rng.random() < 0.5:
            kw = {} if p == P and rng.random() < 0.3 else {"p": p}
            r.check("rank", rows, **kw)
        else:
            w = min((len(x) for x in rows), default=8)
            n = rng.randint(0, max(1, w // 2))
            T0 = set()
            for _ in range(rng.randint(0, 2)):
                T0.add(rng.randint(0, max(0, n - 1)) if n > 0 else 0)
            if rng.random() < 0.08:
                T0.add(rng.choice([-1, -2, n, n + 5, I64MAX, I64MIN]))
            if rng.random() < 0.05:
                T0.add(rng.choice([True, False]))
            kw = {} if p == P and rng.random() < 0.3 else {"p": p}
            r.check("force", rows, n, T0, **kw)
    return r


if __name__ == "__main__":
    variant = sys.argv[1] if len(sys.argv) > 1 else "shipped"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 50000
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 20260905
    m = harness.load_rs(variant)
    r = run(m, f"{variant}/fuzz(seed={seed},n={count})", count, seed)
    sys.exit(1 if r.report() else 0)
