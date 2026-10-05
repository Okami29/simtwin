"""Debug: trace printer 8, the device that reaches PRINTING with a zero target."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

from simtwin.config import SimConfig
from simtwin.fleet.engine import FleetEngine

cfg = SimConfig.default()
eng = FleetEngine(cfg)
P = 8
print("init: state=%d idle_until=%.2f preheat=%.2f T=%.2f elapsed=%.2f dur=%.2f"
      % (eng.state["state"][P], eng.state["idle_until"][P], eng.state["preheat_started"][P],
         eng.state["nozzle_temp_c"][P], eng.state["job_elapsed_s"][P],
         eng.state["job_duration_s"][P]))
for k in range(70):
    eng.step_index = k
    eng.t = (k + 1) * eng.dt
    eng._step_state_machine()
    s = eng.state
    print("t=%3.0f st=%d tgt=%6.1f T=%6.2f bedT=%5.2f preheat=%7.1f idle_until=%7.2f "
          "elapsed=%7.2f dur=%7.2f prog=%.4f"
          % (eng.t, s["state"][P], s["nozzle_target_c"][P], s["nozzle_temp_c"][P],
             s["bed_temp_c"][P], s["preheat_started"][P], s["idle_until"][P],
             s["job_elapsed_s"][P], s["job_duration_s"][P], s["progress"][P]))
    eng._step_thermal()
    eng._step_power_material()
    eng._step_health()
