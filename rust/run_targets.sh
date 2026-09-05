#!/bin/bash
# Long-target runs with the Rust search binary, in Fable's predicted order.
# Logs: /Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/logs/rust-<tag>.log ; combined stdout: /Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/logs/rust-targets.log
B="/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/rust/target/release/kakeya-search"; L="/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/logs"; T=8
run(){ tag=$1; shift; echo "=== $tag  $(date -u +%FT%TZ)  cmd: $*" | tee -a "$L/rust-targets.log"; "$B" "$@" --threads $T > "$L/rust-$tag.log" 2>&1; rc=$?; echo "=== $tag exit=$rc $(date -u +%FT%TZ)" | tee -a "$L/rust-targets.log"; grep -E '^RESULT|TIME LIMIT|strictly-better|best score|tested' "$L/rust-$tag.log" | tail -6 | tee -a "$L/rust-targets.log"; }
run stacked_pool4   stacked --pool 4 --max-t 2 --target 7/4
run stacked_pool6   stacked --pool 6 --max-t 2 --target 7/4
run g2_tall_2x5     g2-tall --rows 5 --max-t 1 --tlimit 7200
run cycles8_pool6   cycles8 --pool 6 --target 67/40 --deg 2 --tlimit 21600
run g2_tall_2x6     g2-tall --rows 6 --max-t 1 --tlimit 14400
echo "=== ALL DONE $(date -u +%FT%TZ)" | tee -a "$L/rust-targets.log"
