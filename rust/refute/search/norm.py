import re, sys
for line in open(sys.argv[1]):
    line = line.rstrip("\n")
    if line.startswith("EXIT="): continue
    line = re.sub(r'"seconds": [0-9.eE+-]+', '"seconds": X', line)
    line = re.sub(r'\[\d+(\.\d+)?s\]', '[Xs]', line)
    print(line)
