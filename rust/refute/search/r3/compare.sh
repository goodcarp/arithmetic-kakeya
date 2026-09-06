#!/bin/bash
# Compare py vs rs1 vs rs12 for one fixture id.
R="/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/rust/refute/search/r3"
O="$R/out"; n=$1
for k in py rs1 rs12; do
  grep -v '^EXIT=' "$O/$n.$k.txt" > "$O/$n.$k.body" 2>/dev/null
  /usr/bin/python3 "$R/mynorm.py" "$O/$n.$k.body" > "$O/$n.$k.norm"
done
echo "### $n   lines: py=$(wc -l < "$O/$n.py.norm") rs1=$(wc -l < "$O/$n.rs1.norm") rs12=$(wc -l < "$O/$n.rs12.norm")"
echo "-- exit codes: py=$(grep -h '^EXIT=' "$O/$n.py.txt") rs1=$(grep -h '^EXIT=' "$O/$n.rs1.txt") rs12=$(grep -h '^EXIT=' "$O/$n.rs12.txt")"
echo "-- rs1 vs rs12 (RAW BYTES, no normalisation):"
if diff -q "$O/$n.rs1.body" "$O/$n.rs12.body" >/dev/null; then echo "   BYTE-IDENTICAL"; else
  diff "$O/$n.rs1.body" "$O/$n.rs12.body" | head -8
  echo "   (normalised:)"; diff -q "$O/$n.rs1.norm" "$O/$n.rs12.norm" >/dev/null && echo "   IDENTICAL after masking seconds" || diff "$O/$n.rs1.norm" "$O/$n.rs12.norm" | head -20
fi
echo "-- py vs rs1 (seconds masked):"
if diff -q "$O/$n.py.norm" "$O/$n.rs1.norm" >/dev/null; then echo "   IDENTICAL ($(wc -l < "$O/$n.py.norm") lines)"; else diff "$O/$n.py.norm" "$O/$n.rs1.norm" | head -30; fi
echo "-- py vs rs12 (seconds masked):"
if diff -q "$O/$n.py.norm" "$O/$n.rs12.norm" >/dev/null; then echo "   IDENTICAL"; else diff "$O/$n.py.norm" "$O/$n.rs12.norm" | head -30; fi
echo "-- RESULT json, field by field (py vs rs12):"
/usr/bin/python3 "$R/jsondiff.py" "$O/$n.py.body" "$O/$n.rs12.body" seconds
echo
