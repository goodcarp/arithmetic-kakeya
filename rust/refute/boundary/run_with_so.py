"""Load a specific fastcore_rs .so into sys.modules, then exec a probe script."""
import importlib.util, sys, os, runpy
so, script = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
spec = importlib.util.spec_from_file_location("fastcore_rs", so)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
sys.modules["fastcore_rs"] = m
sys.argv = [script]
runpy.run_path(script, run_name="__main__")
