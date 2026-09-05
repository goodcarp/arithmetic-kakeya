"""Collect every scan log into results.json and print a markdown summary table."""
import sys, os, json, glob
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def collect():
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "logs", "*.log"))):
        for line in open(f):
            if line.startswith("RESULT "):
                rows.append(json.loads(line[7:]))
    return rows

if __name__ == "__main__":
    rows = collect()
    print("| job | box | slopes | max |T| | target | scanned / total | complete | best score | hits |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        d = "x".join(str(x) for x in r.get("d", []))
        print(f"| {r.get('tag')} | {d} | {r.get('pool','-')} | {r.get('max_t','-')} | "
              f"{r.get('target','-')} | {r.get('scanned')} / {r.get('total')} | "
              f"{'yes' if r.get('complete') else 'no'} | {r.get('best') or r.get('best_score') or '—'} | "
              f"{r.get('hits', r.get('forcing_objects','-'))} |")
    # splice the table into the workbench
    tbl = ["| job | box | slopes | max \\|T\\| | target | scanned / total | complete | best | hits |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        d = "x".join(str(x) for x in r.get("d", []))
        tbl.append(f"| `{r.get('tag')}` | `{d}` | {r.get('pool','-')} | {r.get('max_t','-')} | "
                   f"{r.get('target','r=0')} | {r.get('scanned')} / {r.get('total')} | "
                   f"{'**yes**' if r.get('complete') else 'no'} | "
                   f"{r.get('best') or r.get('best_score') or '(none)'} | "
                   f"{r.get('hits', r.get('forcing_objects','-'))} |")
    wb = os.path.join(ROOT, "KAKEYA-WORKBENCH.md")
    txt = open(wb).read()
    if "TABLE_PLACEHOLDER" in txt:
        open(wb, "w").write(txt.replace("TABLE_PLACEHOLDER", "\n".join(tbl)))
        print("spliced table into KAKEYA-WORKBENCH.md")
    out = json.load(open(os.path.join(ROOT, "results.json")))
    out["scans"] = rows
    json.dump(out, open(os.path.join(ROOT, "results.json"), "w"), indent=2)
    print()
    print("wrote results.json with", len(rows), "scan records")
