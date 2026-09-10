import numpy as np

from utils.recipe import CELL_COUNT, IDLE_MV


def tap_resistance(measurements, bench, log):
    """Series resistance of every sense tap: bleed current through the tap
    path drops the voltage the AFE sees, the simulator's Kelvin sense does
    not move. R = dV / I_bleed, one channel at a time."""
    bench.force_cells([IDLE_MV] * CELL_COUNT)
    idle = np.array(bench.dut_read_cells_mv())
    r_mohm = np.zeros(CELL_COUNT)
    for ch in range(1, CELL_COUNT + 1):
        bench.dut_balance(ch, True)
        loaded = bench.dut_read_cells_mv()[ch - 1]
        i_ma = bench.sim_channel_current_ma(ch)
        bench.dut_balance(ch, False)
        r_mohm[ch - 1] = (idle[ch - 1] - loaded) / i_ma * 1000.0

    measurements.tap_path.x_axis = list(range(1, CELL_COUNT + 1))
    measurements.tap_path.y_axis.resistance = r_mohm.round(1).tolist()
    measurements.tap_path.y_axis.resistance.aggregations.max_mohm = float(r_mohm.max())
    worst = int(r_mohm.argmax()) + 1
    log.info(f"Tap resistance {r_mohm.min():.0f} .. {r_mohm.max():.0f} mOhm, worst channel {worst}")
