"""Regenerate the four uncovered hit lines from the PYTHON drivers' own print
statements (extracted from the source with `ast`, never retyped) and diff them
against the Rust formatters' output echoed by fmtdump.

usage: fmtcheck.py <fmtdump output file>
"""
import sys, os, ast, io, json, contextlib
SRC = "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src"
DRV = "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/rust/oracle_drivers.py"
from fractions import Fraction

def grab(path, marker):
    """Source text of the first `print(...)` call whose source contains marker."""
    text = open(path).read()
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
           and node.func.id == "print":
            seg = ast.get_source_segment(text, node)
            if seg and marker in seg:
                return seg
    raise SystemExit(f"marker {marker!r} not found in {path}")

STMT = {
    "G2":  grab(os.path.join(SRC, "g2_tall.py"), "] score "),
    "C8P": grab(os.path.join(SRC, "cycles8.py"), "new best "),
    "C8H": grab(DRV, "HITOBJ"),
    "ST":  grab(DRV, 'print("      ", x)'),
    "RZ":  grab(os.path.join(SRC, "rzero.py"), "generator-free forcing object!"),
}
for k, v in STMT.items():
    print(f"# {k} <- {v!r}", file=sys.stderr)

class G_: pass

def run_stmt(src, ns):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(src, ns)
    return buf.getvalue().rstrip("\n")

def parse_labs(s):
    if s == "-": return ()
    return tuple(tuple(int(z) for z in p.split(",")) for p in s.split(";"))
def parse_gens(s):
    if s == "-": return []
    out = []
    for p in s.split(";"):
        j, ab = p.split(":")
        a, b = ab.split(",")
        out.append((int(j), (int(a), int(b))))
    return out
def parse_ints(s):
    if s == "-": return []
    return [int(z) for z in s.split(",")]

lines = open(sys.argv[1]).read().splitlines()
i = 0
bad = 0; n = 0
while i < len(lines):
    assert lines[i].startswith("CASE "), lines[i]
    kv = dict(p.split("=", 1) for p in lines[i].split()[2:])
    num = int(kv["num"]); den = int(kv["den"]); m = int(kv["m"])
    t = int(kv["t"]); rows_ = int(kv["rows"])
    labs = parse_labs(kv["LABS"]); gens = parse_gens(kv["GENS"])
    T0 = parse_ints(kv["T0"]); pattern = tuple(parse_ints(kv["PAT"]))
    sc = Fraction(num, den)
    G = G_(); G.m = m
    got = {}
    for j in range(1, 6):
        tag, rest = lines[i + j].split(" ", 1)
        got[tag] = rest
    ns_common = dict(sc=sc, gens=gens, t=t, labs=labs, labels=labs, m=m, n=8,
                     rows_=rows_, G=G, pattern=pattern, json=json, flush=True)
    exp = {}
    exp["G2"]  = run_stmt(STMT["G2"], dict(ns_common))[len("  "):] if False else run_stmt(STMT["G2"], dict(ns_common))
    exp["C8P"] = run_stmt(STMT["C8P"], dict(ns_common))
    x_hit = (str(sc), pattern, labs, gens, sorted(T0))
    ns = dict(ns_common); ns["x"] = x_hit
    exp["C8H"] = run_stmt(STMT["C8H"], ns)[len("HITOBJ "):]
    x_st = (sc, labs, m, gens, sorted(T0))
    ns = dict(ns_common); ns["x"] = x_st
    exp["ST"]  = run_stmt(STMT["ST"], ns)
    exp["RZ"]  = run_stmt(STMT["RZ"], dict(ns_common))
    # fmtdump prints "TAG " + line and we split on the FIRST space only, so
    # every leading space of the line itself is already preserved in `rest`.
    for tag in ("G2", "C8P", "C8H", "ST", "RZ"):
        n += 1
        if got[tag] != exp[tag]:
            bad += 1
            print(f"MISMATCH case {kv} tag {tag}\n  py={exp[tag]!r}\n  rs={got[tag]!r}")
    i += 6
print(f"fmtcheck: {n} formatted lines compared, {bad} mismatches")
