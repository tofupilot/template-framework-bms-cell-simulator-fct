import numpy as np

from utils.recipe import CELL_COUNT, SWEEP_MV

AVERAGES = 8  # conversions averaged per point, both sides of the fixture


def gain_offset_sweep(measurements, bench, log):
    """Three points across the cell range on every channel. Gain error comes
    from the end points, offset from the mean residual, so one number each
    per channel instead of a fit extrapolated to 0 V."""
    truth = []
    reported = []
    for mv in SWEEP_MV:
        bench.force_cells([mv] * CELL_COUNT)
        truth.append(np.mean([bench.sim_readback_mv() for _ in range(AVERAGES)], axis=0))
        reported.append(np.mean([bench.dut_read_cells_mv() for _ in range(AVERAGES)], axis=0))
    truth = np.array(truth)  # (points, channels)
    reported = np.array(reported)

    gain_err_pct = ((reported[-1] - reported[0]) / (truth[-1] - truth[0]) - 1.0) * 100.0
    offset_mv = (reported - truth).mean(axis=0)

    measurements.linearity.x_axis = list(range(1, CELL_COUNT + 1))
    measurements.linearity.y_axis.gain_err = gain_err_pct.round(4).tolist()
    measurements.linearity.y_axis.gain_err.aggregations.max_abs_pct = float(np.abs(gain_err_pct).max())
    measurements.linearity.y_axis.offset = offset_mv.round(2).tolist()
    measurements.linearity.y_axis.offset.aggregations.max_abs_mv = float(np.abs(offset_mv).max())
    log.info(f"Gain error up to {np.abs(gain_err_pct).max():.3f} %, offset up to {np.abs(offset_mv).max():.2f} mV")
