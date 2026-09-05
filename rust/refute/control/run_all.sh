#!/bin/sh
# Control-flow / ordering refutation battery.  Run from this directory.
set -e
cd "$(dirname "$0")"
PY=/usr/bin/python3
$PY -u test_control.py
$PY -u test_state.py
$PY -u test_dfs_aliasing.py
$PY -u test_threads.py
for s in 20260905 1 2 7 4242; do $PY -u fuzz_control.py $s 25000; done
for s in 11 12 13;            do $PY -u fuzz_ragged.py  $s 30000; done
for s in 5 6 77;              do $PY -u fuzz_pivot.py   $s 12000; done
