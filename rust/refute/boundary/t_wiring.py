"""Wiring probes for the fastcore -> fastcore_rs drop-in.

Checks (each prints CHECK <name> PASS/FAIL/INFO):
  * src/fastcore.py = 2976-byte original + a 461-byte appended block, and the
    2976-byte prefix is a self-consistent 109-line module (the pre-edit file).
  * KAKEYA_PURE_PY=1 really reaches the pure Python.
  * _force_py / _rank_py are the pure implementations, not the Rust ones.
  * with the env var unset, fastcore.force is the Rust one.
  * which in-tree tests actually reach fastcore at all.
  * the ImportError swallow: a broken .so degrades silently to pure Python.
"""
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TESTS = os.path.join(ROOT, "tests")
PY39 = "/usr/bin/python3"
PY312 = "/usr/local/bin/python3.12"

fails = []


def chk(name, cond, extra=""):
    print(("PASS  " if cond else "FAIL  ") + name + (("  " + str(extra)) if extra else ""))
    if not cond:
        fails.append(name)


def info(name, extra):
    print("INFO  " + name + "  " + str(extra))


def run(py, code, env=None, cwd=SRC):
    e = dict(os.environ)
    e.pop("KAKEYA_PURE_PY", None)
    if env:
        e.update(env)
    r = subprocess.run([py, "-c", code], capture_output=True, text=True, env=e, cwd=cwd)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


# ---------------------------------------------------------------- file split
raw = open(os.path.join(SRC, "fastcore.py"), "rb").read()
orig = raw[:2976]
tail = raw[2976:]
chk("fastcore.py splits at 2976 bytes into original + appended block",
    orig.endswith(b"        rk += 1\n    return rk\n") and tail.startswith(b"\n\n# --- Rust drop-in"),
    "orig=%d tail=%d" % (len(orig), len(tail)))
chk("reconstructed original is 109 lines", orig.count(b"\n") == 109, orig.count(b"\n"))
info("sha256(reconstructed original)", hashlib.sha256(orig).hexdigest())
info("appended block", repr(tail.decode())[:120] + "...")
chk("appended block does not touch anything above it",
    b"def force" not in tail and b"def rank" not in tail and b"_INV" not in tail)
chk("no other src/*.py was given a Rust hook",
    all(b"fastcore_rs" not in open(os.path.join(SRC, f), "rb").read()
        for f in os.listdir(SRC) if f.endswith(".py") and f != "fastcore.py"))

# ---------------------------------------------------------------- env switch
probe = ("import fastcore,sys;"
         "print(fastcore.force.__module__, fastcore.rank.__module__,"
         " fastcore._force_py.__module__, fastcore._rank_py.__module__)")
rc, out, err = run(PY39, probe)
chk("py3.9 default: fastcore.force is the Rust one", out.split()[:2] == ["fastcore_rs", "fastcore_rs"],
    out or err)
chk("py3.9 default: _force_py/_rank_py stay pure Python",
    out.split()[2:] == ["fastcore", "fastcore"], out or err)

rc, out, err = run(PY39, probe, env={"KAKEYA_PURE_PY": "1"})
chk("KAKEYA_PURE_PY=1 gives pure Python for all four",
    out.split() == ["fastcore"] * 4, out or err)

for v in ("0", "", "true", "yes", "TRUE", "1 "):
    rc, out, err = run(PY39, probe, env={"KAKEYA_PURE_PY": v})
    info("KAKEYA_PURE_PY=%r -> force.__module__" % v, out.split()[0] if out else err)

# ---------------------------------------------------------------- 3.12 import
rc, out, err = run(PY312, probe)
chk("py3.12 (abi3) imports the same .so", out.split()[:2] == ["fastcore_rs", "fastcore_rs"],
    out or err)
rc, out, err = run(PY312, "import fastcore_rs;print(fastcore_rs.__file__, fastcore_rs.P)")
chk("py3.12 loads src/fastcore_rs.abi3.so directly", "fastcore_rs.abi3.so" in out, out or err)

# ---------------------------------------------------------------- silent swallow
bad = os.path.join(HERE, "_shadow")
os.makedirs(bad, exist_ok=True)
open(os.path.join(bad, "fastcore_rs.py"), "w").write("raise ImportError('simulated broken .so')\n")
e = dict(os.environ)
e.pop("KAKEYA_PURE_PY", None)
e["PYTHONPATH"] = bad + os.pathsep + SRC
r = subprocess.run([PY39, "-c", probe], capture_output=True, text=True, env=e, cwd=HERE)
info("broken fastcore_rs on the path -> ", (r.stdout.strip() or r.stderr.strip()))
chk("a broken fastcore_rs degrades to pure Python with NO warning and exit 0",
    r.returncode == 0 and r.stdout.split()[:1] == ["fastcore"] and r.stderr.strip() == "",
    "rc=%d stderr=%r" % (r.returncode, r.stderr.strip()))

# non-ImportError at import time is NOT swallowed
open(os.path.join(bad, "fastcore_rs.py"), "w").write("raise RuntimeError('bad dylib')\n")
r = subprocess.run([PY39, "-c", probe], capture_output=True, text=True, env=e, cwd=HERE)
info("fastcore_rs raising RuntimeError at import",
     "rc=%d out=%r err=%r" % (r.returncode, r.stdout.strip(), r.stderr.strip().splitlines()[-1:] ))
os.remove(os.path.join(bad, "fastcore_rs.py"))

# ---------------------------------------------------------------- test reach
code = (
    "import sys,os;sys.path.insert(0,%r);import fastcore;"
    "hits=[];_f=fastcore.force;_r=fastcore.rank;\n"
    "def wf(*a,**k):\n hits.append('force');return _f(*a,**k)\n"
    "def wr(*a,**k):\n hits.append('rank');return _r(*a,**k)\n"
    "fastcore.force=wf;fastcore.rank=wr\n"
    "import io,contextlib\n"
    "sys.argv=['x']\n"
    "buf=io.StringIO()\n"
    "try:\n"
    " with contextlib.redirect_stdout(buf):\n"
    "  exec(compile(open(%r).read(),%r,'exec'),{'__name__':'__main__','__file__':%r})\n"
    "except SystemExit:\n pass\n"
    "sys.stderr.write('HITS=%%d\\n'%%len(hits))\n"
)
print()
for t in sorted(os.listdir(TESTS)):
    if not t.startswith("test_") or not t.endswith(".py"):
        continue
    path = os.path.join(TESTS, t)
    c = code % (SRC, path, path, path)
    r = subprocess.run([PY39, "-c", c], capture_output=True, text=True, cwd=TESTS,
                       env={k: v for k, v in os.environ.items() if k != "KAKEYA_PURE_PY"})
    n = [ln for ln in r.stderr.splitlines() if ln.startswith("HITS=")]
    info("test %-28s module-level fastcore.force/rank calls" % t, n[0] if n else "n/a " + r.stderr[-200:])

print()
print("FAILS:", fails if fails else "none")
sys.exit(1 if fails else 0)
