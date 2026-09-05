import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
from fractions import Fraction
from search import scan_dims, POOL4, POOL5, POOL6

TARGET = Fraction(67, 40)   # 1.675

def run(tag, dims, pool, max_t=0, limit=None, seed=0, tlimit=600):
    out = []
    for d in dims:
        h, b, c, tot, el = scan_dims(d, pool, TARGET, max_t=max_t, limit=limit,
                                     seed=seed, tlimit=tlimit, verbose=True)
        rec = {"tag": tag, "d": d, "pool": [list(x) for x in pool], "max_t": max_t,
               "scanned": c, "total": tot, "best": str(b) if b else None,
               "hits": len(h), "seconds": round(el, 1)}
        print("RESULT", json.dumps(rec), flush=True)
        out.append(rec)
        for hh in h:
            print("HITOBJ", json.dumps({k: (str(v) if k == "score" else
                   ([list(x) for x in v] if k == "labels" else
                    [[g[0], list(g[1])] for g in v] if k == "gens" else v))
                   for k, v in hh.items()}), flush=True)
    return out

# extra entry point: look for anything strictly better than 7/4 (not only <=1.675)
def run_beat175():
    import search
    global TARGET
    from fractions import Fraction as F
    search_target = F(12, 7)
    for d, mt, lim in ([[2,2,2], 1, 6000], [[2,4], 1, 4000], [[4,2], 1, 4000],
                       [[2,2,2], 0, 6000]):
        h, b, c, tot, el = scan_dims(d, POOL4, search_target, max_t=mt,
                                     limit=lim, seed=7, tlimit=700, verbose=True)
        print("RESULT", json.dumps({"tag": "beat175", "d": d, "max_t": mt,
              "scanned": c, "best": str(b) if b else None, "hits": len(h),
              "seconds": round(el, 1)}), flush=True)
        for hh in h:
            print("HITOBJ", json.dumps({k: (str(v) if k == "score" else
                   ([list(x) for x in v] if k == "labels" else
                    [[g[0], list(g[1])] for g in v] if k == "gens" else v))
                   for k, v in hh.items()}), flush=True)


if __name__ == "__main__":
    which = sys.argv[1]
    if which == "n6":
        run("n6", [[2,3],[3,2],[6]], POOL4, max_t=0, tlimit=800)
        run("n6t1", [[2,3],[3,2]], POOL4, max_t=1, tlimit=800)
    elif which == "n8":
        run("n8", [[2,2,2]], POOL4, max_t=0, limit=30000, seed=1, tlimit=2400)
    elif which == "n8t":
        run("n8t1", [[2,2,2]], POOL4, max_t=1, limit=8000, seed=2, tlimit=2400)
    elif which == "beat175":
        run_beat175()
    elif which == "n4pool6":
        from fractions import Fraction as _F
        for d in ([2,2],[4]):
            for mt in (0,1):
                h,b,c,tot,el = scan_dims(d, POOL6, _F(7,4), max_t=mt, tlimit=900, verbose=True)
                print("RESULT", json.dumps({"tag":"n4pool6","d":d,"max_t":mt,
                      "scanned":c,"total":tot,"best":str(b) if b else None,
                      "hits":len(h),"seconds":round(el,1)}), flush=True)
