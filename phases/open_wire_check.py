from utils.recipe import CELL_COUNT, IDLE_MV, OPEN_WIRE_CHANNEL


def open_wire_check(measurements, bench, log):
    """Open one simulator channel and require the DUT to flag the wire, not
    report a plausible voltage. Then reconnect and require a clean fault map."""
    bench.force_cells([IDLE_MV] * CELL_COUNT)
    bench.open_channel(OPEN_WIRE_CHANNEL)
    reported = bench.dut_read_cells_mv()
    faults = bench.dut_read_faults()
    flagged = OPEN_WIRE_CHANNEL in faults["open_wire"]
    log.info(f"Channel {OPEN_WIRE_CHANNEL} open: DUT reads {reported[OPEN_WIRE_CHANNEL - 1]:.1f} mV, "
             f"open-wire flags {faults['open_wire']}")
    measurements.open_wire_flagged = flagged
    measurements.open_wire_reading_mv = float(reported[OPEN_WIRE_CHANNEL - 1])

    bench.close_channel(OPEN_WIRE_CHANNEL)
    measurements.faults_after_reconnect = bench.dut_read_faults()
