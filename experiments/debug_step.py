"""Debug: find the first PRINTING sample with a zero nozzle target."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from simtwin.config import SimConfig
from simtwin.fleet.engine import FleetEngine, PRE, PRINT

cfg = SimConfig.default()
eng = FleetEngine(cfg)
n_steps = cfg.n_steps
hist: list[tuple] = []
found = None
for k in range(n_steps):
    eng.step_index = k
    eng.t = (k + 1) * eng.dt
    eng._step_state_machine()
    st = eng.state["state"]
    tgt = eng.state["nozzle_target_c"]
    bad = np.nonzero((st == PRINT) & (tgt == 0.0))[0]
    if bad.size and found is None:
        found = (eng.t, int(bad[0]))
        print("FIRST bad at t=%.0f printer=%d" % (eng.t, bad[0]))
        break
    eng._step_thermal()
    eng._step_power_material()
    eng._step_health()
    i = 3
    hist.append((eng.t, int(st[i]), float(tgt[i]), float(eng.state["nozzle_temp_c"][i]),
                 float(eng.state["preheat_started"][i]), float(eng.state["idle_until"][i])))

for row in hist[:30]:
    print("t=%4.0f state=%d target=%6.1f T=%6.2f preheat=%7.1f idle_until=%7.1f" % row)
print("...")
for row in hist[-20:]:
    print("t=%4.0f state=%d target=%6.1f T=%6.2f preheat=%7.1f idle_until=%7.1f" % row)
print("found:", found)
