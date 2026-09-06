#!/bin/bash
SRC="/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src"
O="/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/rust/refute/search/r3/out"
mkdir -p "$O"
run(){ n=$1; shift; ( cd "$SRC" && KAKEYA_PURE_PY=1 /usr/bin/python3 "$@" ) > "$O/$n.py.txt" 2>&1; echo "EXIT=$?" >> "$O/$n.py.txt"; }
run "$1" "${@:2}"
