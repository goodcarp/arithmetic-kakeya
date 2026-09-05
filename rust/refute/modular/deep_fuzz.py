"""Deeper fuzz: long pivot chains at composite moduli, plus buffer-reuse and
idempotency checks on the Rust's thread-local scratch.

Rationale for the lens: the port replaces Python's arbitrary-precision `%` and
`pow(a, p-2, p)` with u64 rem_euclid + a binary modexp.  The place that would
break is a *deep* elimination at a composite modulus, where the "inverse" is
garbage that must nonetheless be reproduced bit for bit, and where every
intermediate a*b must stay under 2^64.  So: dense matrices, entries drawn from
the whole of [0, p), several pivots, and moduli right under 2^32.
"""
import random
import sys

sys.path.insert(0, ".")
import harness

P = (1 << 31) - 1
BIG = [4294967295, 4294967294, 4294967293, 4294967291, 4294967279,
       4294901761, 4294967296 - 7, 3000000021, 2147483648, 2147483649, P,
       2147483629, 4000000007]
SMALL = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 25, 27, 32, 49, 64, 91, 100,
         121, 128, 210, 255, 256, 257, 1009, 65535, 65536, 65537]


def dense(rng, p, nr, w):
    """Entries spread over the whole residue range, plus exact multiples of p
    and p +/- 1 so the reduction boundary is hit inside a deep elimination."""
    out = []
    for _ in range(nr):
        row = []
        for _ in range(w):
            k = rng.random()
            if k < 0.55:
                row.append(rng.randrange(p) if p > 1 else 0)
            elif k < 0.70:
                row.append(-(rng.randrange(p)) if p > 1 else 0)
            elif k < 0.80:
                row.append(p - 1)
            elif k < 0.88:
                row.append(p * rng.randint(-3, 3) + rng.randint(-1, 1))
            elif k < 0.94:
                row.append(rng.randint(-3, 3))
            else:
                row.append(rng.choice([(1 << 62), -(1 << 62), (1 << 63) - 1,
                                       -(1 << 63)]))
        out.append(row)
    return out


def run(mod, label, count, seed):
    rng = random.Random(seed)
    r = harness.Runner(mod, label)
    prev = None
    for i in range(count):
        p = rng.choice(BIG if rng.random() < 0.5 else SMALL)
        w = rng.choice([2, 4, 6, 8, 10, 12, 16])
        nr = rng.randint(1, 10)
        rows = dense(rng, p, nr, w)
        if rng.random() < 0.5:
            r.check("rank", rows, p=p)
        else:
            n = w // 2
            T0 = set(rng.sample(range(n), rng.randint(0, min(n, 2)))) if n else set()
            r.check("force", rows, n, T0, p=p)
        # buffer reuse: repeat the previous call after a differently-shaped one
        # and demand the same answer (a dirty thread-local scratch shows here).
        if prev is not None and i % 7 == 0:
            r.check(*prev[0], **prev[1])
        prev = ((("rank", rows), {"p": p}) if rng.random() < 0.5
                else (("force", rows, w // 2, set()), {"p": p}))
        prev = (prev[0], prev[1])
    return r


if __name__ == "__main__":
    variant = sys.argv[1] if len(sys.argv) > 1 else "shipped"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 25000
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    m = harness.load_rs(variant)
    r = run(m, f"{variant}/deep(seed={seed},n={count})", count, seed)
    sys.exit(1 if r.report() else 0)
