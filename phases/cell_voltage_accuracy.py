import numpy as np

from utils.recipe import STAIRCASE_MV


def cell_voltage_accuracy(measurements, bench, log):
    """Force a distinct voltage on every channel, compare the DUT's reading
    against the simulator's readback, and check the readback is monotonic."""
    bench.force_cells(STAIRCASE_MV)
    truth = np.array(bench.sim_readback_mv())
    reported = np.array(bench.dut_read_cells_mv())
    error = reported - truth

    channels = list(range(1, len(truth) + 1))
    measurements.staircase.x_axis = channels
    measurements.staircase.y_axis.forced = truth.tolist()
    measurements.staircase.y_axis.reported = reported.tolist()
    measurements.staircase.y_axis.error = error.round(2).tolist()
    measurements.staircase.y_axis.error.aggregations.max_mv = float(error.max())
    measurements.staircase.y_axis.error.aggregations.min_mv = float(error.min())

    # A crossed pair in the sense harness breaks the staircase order.
    order_ok = bool(np.all(np.diff(reported) > 0))
    measurements.order_ok = order_ok
    worst = int(np.abs(error).argmax()) + 1
    log.info(f"Error {error.min():+.2f} .. {error.max():+.2f} mV, worst channel {worst}, order {'ok' if order_ok else 'BROKEN'}")
