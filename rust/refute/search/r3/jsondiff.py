"""Field-by-field diff of every RESULT json object in two streams."""
import json, sys

def results(path):
    out = []
    for line in open(path):
        line = line.strip()
        if line.startswith("RESULT "):
            out.append(json.loads(line[len("RESULT "):]))
    return out

a, b = results(sys.argv[1]), results(sys.argv[2])
ignore = set(sys.argv[3:]) or {"seconds"}
if len(a) != len(b):
    print("RESULT-COUNT MISMATCH %d vs %d" % (len(a), len(b))); sys.exit(2)
bad = 0
for i, (x, y) in enumerate(zip(a, b)):
    keys = sorted(set(x) | set(y))
    for k in keys:
        if k in ignore:
            print("  [%d] %-10s IGNORED  %r / %r" % (i, k, x.get(k), y.get(k))); continue
        if k not in x or k not in y:
            print("  [%d] %-10s ONLY-IN-ONE  a=%r b=%r" % (i, k, x.get(k, "<absent>"), y.get(k, "<absent>"))); bad += 1; continue
        mark = "OK " if x[k] == y[k] else "DIFF"
        if x[k] != y[k]: bad += 1
        print("  [%d] %-10s %s  %r / %r" % (i, k, mark, x[k], y[k]))
print("JSON FIELD DIFFS:", bad)
sys.exit(1 if bad else 0)
