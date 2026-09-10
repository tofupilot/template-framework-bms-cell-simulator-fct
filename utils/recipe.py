"""Bench recipe shared by the phases and the mock: channel count, the staircase
pattern, the three-point sweep and the limits the phases derive numbers from."""

CELL_COUNT = 16

# Distinct voltage per channel. Equal voltages on every channel cannot reveal a
# crossed sense harness; a monotonic staircase makes a swap visible as a
# non-monotonic readback.
STAIRCASE_MV = [3200 + 60 * i for i in range(CELL_COUNT)]  # 3200 .. 4100 mV

# Three points across the cell range separate gain error from offset.
SWEEP_MV = [3000, 3600, 4200]

# Voltage the pack sits at while the bench talks to the DUT.
IDLE_MV = 3600

# Channel opened on the simulator side for the open-wire check (1-based).
OPEN_WIRE_CHANNEL = 8
