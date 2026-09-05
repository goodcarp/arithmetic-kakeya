"""Small-matrix mod-p forcing engine (pure Python; faster than numpy at these sizes).

force(rows, n, T0) -> (ok, T).  rows are length-2n integer lists.
Per round: row-reduce the restriction of the module to the *unforced*
coordinates once, then test membership of delta_v (x) (1,-1) for every
unforced v.  Monotone in T and in rows, so callers may warm-start.
"""
P = (1 << 31) - 1
_INV = {}


def _inv(a, p=P):
    v = _INV.get(a)
    if v is None:
        v = pow(a, p - 2, p)
        _INV[a] = v
    return v


def force(rows, n, T0, p=P):
    T = set(T0)
    while len(T) < n:
        U = [j for j in range(n) if j not in T]
        pos = {j: i for i, j in enumerate(U)}
        w = 2 * len(U)
        B = []
        for r in rows:
            row = [0] * w
            nz = False
            for j in U:
                a = r[2 * j] % p
                b = r[2 * j + 1] % p
                if a or b:
                    nz = True
                    i2 = 2 * pos[j]
                    row[i2] = a
                    row[i2 + 1] = b
            if nz:
                B.append(row)
        piv = []
        rk = 0
        nB = len(B)
        for c in range(w):
            if rk >= nB:
                break
            sel = -1
            for i in range(rk, nB):
                if B[i][c]:
                    sel = i
                    break
            if sel < 0:
                continue
            B[rk], B[sel] = B[sel], B[rk]
            iv = _inv(B[rk][c], p)
            B[rk] = [(x * iv) % p for x in B[rk]]
            pr = B[rk]
            for i in range(nB):
                if i != rk and B[i][c]:
                    fac = B[i][c]
                    B[i] = [(a - fac * b) % p for a, b in zip(B[i], pr)]
            piv.append(c)
            rk += 1
        found = None
        for j in U:
            i2 = 2 * pos[j]
            v = [0] * w
            v[i2] = 1
            v[i2 + 1] = p - 1
            for q, c in enumerate(piv):
                if v[c]:
                    fac = v[c]
                    pr = B[q]
                    v = [(a - fac * b) % p for a, b in zip(v, pr)]
            if not any(v):
                found = j
                break
        if found is None:
            return False, T
        T.add(found)
    return True, T


def rank(rows, p=P):
    if not rows:
        return 0
    B = [[x % p for x in r] for r in rows]
    w = len(B[0])
    rk = 0
    nB = len(B)
    for c in range(w):
        if rk >= nB:
            break
        sel = -1
        for i in range(rk, nB):
            if B[i][c]:
                sel = i
                break
        if sel < 0:
            continue
        B[rk], B[sel] = B[sel], B[rk]
        iv = _inv(B[rk][c], p)
        B[rk] = [(x * iv) % p for x in B[rk]]
        pr = B[rk]
        for i in range(rk + 1, nB):
            if B[i][c]:
                fac = B[i][c]
                B[i] = [(a - fac * b) % p for a, b in zip(B[i], pr)]
        rk += 1
    return rk
