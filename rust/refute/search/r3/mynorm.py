# Independent normaliser (written for r3, not reusing refute/search/norm.py).
# Masks ONLY wall-clock timings: the RESULT json "seconds" field and [<x>s].
# Everything else -- scores, witnesses, counts, tie-breaks -- is compared verbatim.
import re, sys
for line in open(sys.argv[1]):
    line = line.rstrip("\n")
    line = re.sub(r'("seconds":\s*)[-+0-9.eE]+', r'\1SEC', line)
    line = re.sub(r'\[\s*[0-9]+(\.[0-9]+)?s\s*\]', '[SEC]', line)
    print(line)
