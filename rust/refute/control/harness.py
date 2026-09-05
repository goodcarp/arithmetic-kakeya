"""Shared differential harness: pure-Python fastcore vs fastcore_rs.

Every reference evaluation clears fastcore._INV first (S1 sec 2.1 hard
requirement).  Results are normalised to a comparable value:
  ("force", ok, sorted(T))  |  ("rank", int)  |  ("raise", ExcTypeName)
"""
import sys, os

SRC = "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src"
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import fastcore
import fastcore_rs

py_force = fastcore._force_py
py_rank = fastcore._rank_py
rs_force = fastcore_rs.force
rs_rank = fastcore_rs.rank

P = fastcore.P


def _norm_force(res):
    ok, T = res
    return ("force", bool(ok), type(ok).__name__, sorted(T), type(T).__name__)


def call_py_force(*a, **kw):
    fastcore._INV.clear()
    try:
        return _norm_force(py_force(*a, **kw))
    except Exception as e:
        return ("raise", type(e).__name__)


def call_rs_force(*a, **kw):
    try:
        return _norm_force(rs_force(*a, **kw))
    except Exception as e:
        return ("raise", type(e).__name__)


def call_py_rank(*a, **kw):
    fastcore._INV.clear()
    try:
        return ("rank", py_rank(*a, **kw))
    except Exception as e:
        return ("raise", type(e).__name__)


def call_rs_rank(*a, **kw):
    try:
        return ("rank", rs_rank(*a, **kw))
    except Exception as e:
        return ("raise", type(e).__name__)


class Results:
    def __init__(self, name):
        self.name = name
        self.n = 0
        self.div = []

    def cmp(self, label, pyres, rsres):
        self.n += 1
        if pyres != rsres:
            self.div.append((label, pyres, rsres))
            return False
        return True

    def report(self):
        print("== %s: %d checks, %d divergences" % (self.name, self.n, len(self.div)))
        def _t(x, k=240):
            r = repr(x)
            return r if len(r) <= k else r[:k] + "...<%d chars>" % len(r)
        for label, a, b in self.div:
            print("   DIVERGE %s" % _t(label, 400))
            print("      py = %s" % _t(a))
            print("      rs = %s" % _t(b))
        return len(self.div)
