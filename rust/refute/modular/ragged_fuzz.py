"""Ragged rows inside deep eliminations, at every kind of modulus.

`rank` takes its width from rows[0] only, so a later short row raises
IndexError and a later long row is silently truncated by `zip`.  The Rust
reproduces the truncation by *mutating* the row (`row.truncate(pr.len())`),
which is the most intricate divergence risk in the port, and it interacts with
the modulus because the truncation only happens on rows whose pivot entry is
nonzero mod p.  So: ragged widths, many pivots, and moduli that make entries
vanish.

Also covers production-shaped inputs: n up to 16 (w = 32), entries in -3..3,
which is exactly what build_rows/gen_row can emit.
"""
import random
import sys

sys.path.insert(0, ".")
import harness

P = (1 << 31) - 1
MODULI = [1, 2, 3, 4, 5, 7, 8, 9, 91, 128, 256, 257, 65536, 65537,
          2147483629, P, 2147483648, 2147483649, 3000000021,
          4294967291, 4294967294, 4294967295]
# The only coordinates any pool can emit, with the sign flip from build_rows.
PROD = [-3, -2, -1, 0, 1, 2, 3]


def ragged_case(rng, p):
    w0 = rng.randint(0, 14)
    rows = [[rng.choice([rng.randrange(p) if p > 1 else 0,
                         p * rng.randint(-2, 2),
                         p - 1, p + 1, rng.randint(-3, 3)])
             for _ in range(w0)]]
    for _ in range(rng.randint(0, 8)):
        ww = max(0, w0 + rng.randint(-3, 3))
        rows.append([rng.choice([rng.randrange(p) if p > 1 else 0,
                                 p * rng.randint(-2, 2),
                                 p - 1, rng.randint(-3, 3)])
                     for _ in range(ww)])
    return rows


def prod_case(rng):
    n = rng.randint(1, 16)
    w = 2 * n
    rows = []
    for _ in range(rng.randint(0, 3 * n)):
        row = [0] * w
        if rng.random() < 0.75:                 # an edge row: two vertices
            u, v = rng.sample(range(n), 2) if n >= 2 else (0, 0)
            x = rng.choice([(1, 0), (0, 1), (1, 1), (1, 2), (1, 3),
                            (2, 1), (1, -2), (3, 1)])
            row[2 * u] += x[0]; row[2 * u + 1] += x[1]
            row[2 * v] -= x[0]; row[2 * v + 1] -= x[1]
        else:                                   # a generator row
            j = rng.randrange(n)
            x = rng.choice([(1, 0), (0, 1), (1, 1), (1, 2), (1, 3),
                            (2, 1), (1, -2), (3, 1)])
            row[2 * j] = x[0]; row[2 * j + 1] = x[1]
        rows.append(row)
    return n, rows


def run(mod, label, count, seed):
    rng = random.Random(seed)
    r = harness.Runner(mod, label)
    for _ in range(count):
        p = rng.choice(MODULI)
        if rng.random() < 0.5:
            rows = ragged_case(rng, p)
            if rng.random() < 0.6:
                r.check("rank", rows, p=p)
            else:
                n = rng.randint(0, 8)
                r.check("force", rows, n, set(rng.sample(range(max(n, 1)),
                                                         rng.randint(0, 1))), p=p)
        else:
            n, rows = prod_case(rng)
            if rng.random() < 0.4:
                r.check("rank", rows, p=p)
            else:
                t = rng.randint(0, min(n, 3))
                T0 = set(rng.sample(range(n), t))
                r.check("force", rows, n, T0, p=p)
    return r


if __name__ == "__main__":
    variant = sys.argv[1] if len(sys.argv) > 1 else "shipped"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 25000
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 11
    m = harness.load_rs(variant)
    r = run(m, f"{variant}/ragged+prod(seed={seed},n={count})", count, seed)
    sys.exit(1 if r.report() else 0)
