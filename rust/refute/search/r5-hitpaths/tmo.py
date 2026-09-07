#!/usr/bin/env python3
"""tmo.py <seconds> <cmd...> -- run cmd with a wall-clock cap; exit 124 on timeout."""
import subprocess, sys
lim = float(sys.argv[1])
try:
    r = subprocess.run(sys.argv[2:], timeout=lim)
    sys.exit(r.returncode)
except subprocess.TimeoutExpired:
    sys.exit(124)
