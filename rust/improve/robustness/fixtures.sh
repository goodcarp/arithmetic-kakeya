#!/bin/bash
# r3 fixtures F1-F7, P2-P7b, S0, S123 -- run against $BIN, tag $TAGNAME
K="/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/rust"
BIN=$1; O=$2; mkdir -p "$O"
run(){ n=$1; shift; "$BIN" "$@" > "$O/$n.txt" 2>&1; echo "EXIT=$?" >> "$O/$n.txt"; }
run F1  scan --tag n4_p6_t1 --d 2x2 --pool 6 --max-t 1 --target 7/4    --threads $T
run F2  scan --tag g2_23_t1 --d 2x3 --pool 3 --max-t 1 --target 9/5    --threads $T
run F3  scan --tag g2_32_t1 --d 3x2 --pool 3 --max-t 1 --target 9/5    --threads $T
run F4  scan --tag newP --d 2x3 --pool 4 --max-t 1 --target 67/40 --limit 40 --seed 11 --threads $T
run F5  scan --tag newQ --d 2x2 --pool 6 --max-t 1 --target 2          --threads $T
run F6  g2-tall --rows 2 --max-t 1 --threads $T
run F7  g2-tall --rows 3 --max-t 2 --threads $T
run P2  scan --tag P2  --d 2x2 --pool 6 --max-t 1 --target 14/8        --threads $T
run P3  scan --tag P3  --d 2x2 --pool 3 --max-t 1 --target 2 --limit 100 --seed 11 --threads $T
run P4  scan --tag P4  --d 2x2 --pool 6 --max-t 1 --target 7/4 --limit 1 --seed 11 --threads $T
run P5  scan --tag P5  --d 1   --pool 3 --max-t 0 --target 2           --threads $T
run P6  scan --tag P6  --d 2x2 --pool 3 --max-t 3 --target 2           --threads $T
run P7b scan --tag P7b --d 2x2 --pool 4 --max-t 1 --target 2 --limit 37 --seed 11  --threads $T
run S0  scan --tag S0  --d 2x2 --pool 4 --max-t 1 --target 2 --limit 37 --seed 0   --threads $T
run S123 scan --tag S123 --d 2x2 --pool 4 --max-t 1 --target 2 --limit 37 --seed 123 --threads $T
