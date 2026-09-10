from utils.recipe import CELL_COUNT, IDLE_MV


def identify_dut(measurements, bench, unit, log):
    """Setup: bring the simulated pack to 3.6 V/cell and read the DUT's
    identity block. Every main phase talks to the board this phase proved alive."""
    bench.force_cells([IDLE_MV] * CELL_COUNT)
    ident = bench.dut_identify()
    log.info(f"DUT {unit.serial_number}: fw {ident['firmware']}, AFE {ident['afe']} rev {ident['afe_die_rev']}")
    unit.metadata["afe_die_rev"] = ident["afe_die_rev"]

    measurements.firmware_version = ident["firmware"]
    measurements.afe_identity = {"afe": ident["afe"], "cell_count": ident["cell_count"]}
    measurements.config_crc = ident["config_crc"]
