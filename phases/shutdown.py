from utils.recipe import CELL_COUNT, IDLE_MV


def shutdown(measurements, bench, log):
    """Teardown: ship mode, quiescent draw on the 250 uA range, outputs off.
    Runs after a failed main phase too, so no board is left balancing."""
    bench.force_cells([IDLE_MV] * CELL_COUNT)
    bench.dut_ship_mode()
    ship_ua = bench.sim_total_current_ua()
    measurements.ship_current_ua = ship_ua
    log.info(f"Ship mode draw {ship_ua:.1f} uA across the stack")
    bench.outputs_off()
