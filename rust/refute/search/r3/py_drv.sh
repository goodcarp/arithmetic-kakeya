#!/bin/bash
K="/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya"
O="$K/rust/refute/search/r3/out"
n=$1; shift
( cd "$K/src" && KAKEYA_PURE_PY=1 /usr/bin/python3 "$K/rust/oracle_drivers.py" "$@" ) > "$O/$n.py.txt" 2>&1
echo "EXIT=$?" >> "$O/$n.py.txt"
