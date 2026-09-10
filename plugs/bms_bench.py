"""BMS functional test bench (mock): a 16-channel battery cell simulator and
the UART link to the BMS PCBA under test.

Maps to a Chroma 87001-class cell simulator (16 isolated channels, 0-5 V,
bidirectional 5 A, 0.1 mV readback, 500 mA and 250 uA current ranges) plus the
DUT's UART service port. The mock synthesizes a healthy 16S board built on an
external-balancing AFE: per-channel gain and offset inside the datasheet window,
one channel with a slightly higher offset, one sense tap with a marginal crimp.
Swap this class for one speaking SCPI to the simulator and the DUT protocol
over pyserial; the phases stay unchanged.
"""

import numpy as np

from utils.recipe import CELL_COUNT


class BmsBench:
    WEAK_OFFSET_CHANNEL = 11  # zero-based; offset near the top of the window
    WEAK_TAP_CHANNEL = 5  # zero-based; crimp at 115 mOhm instead of ~45

    def __init__(self, cell_count, bleed_ma):
        self.cell_count = int(cell_count)
        self.bleed_ma = float(bleed_ma)
        self._rng = np.random.default_rng(87001)
        # AFE per-channel error model, inside BQ79616-class -3.0/+2.4 mV window.
        self._gain = 1.0 + self._rng.normal(0.0, 1.2e-4, self.cell_count)
        self._offset_mv = self._rng.normal(0.0, 0.6, self.cell_count)
        self._offset_mv[self.WEAK_OFFSET_CHANNEL] = 1.9
        self._gain[self.WEAK_OFFSET_CHANNEL] = 1.0 + 2.0e-4
        # Sense tap path: harness wire, connector pin, solder joint (mOhm).
        self._tap_mohm = 45.0 + self._rng.normal(0.0, 8.0, self.cell_count)
        self._tap_mohm[self.WEAK_TAP_CHANNEL] = 115.0
        self._forced_mv = np.zeros(self.cell_count)
        self._open = np.zeros(self.cell_count, dtype=bool)
        self._balancing = np.zeros(self.cell_count, dtype=bool)
        self._ship_mode = False
        # self.sim = pyvisa.ResourceManager().open_resource("TCPIP0::192.168.1.60::INSTR")
        # self.dut = serial.Serial("/dev/ttyUSB0", 1_000_000, timeout=0.2)
        print(f"Cell simulator connected, {self.cell_count} channels, outputs off")

    # --- simulator side -------------------------------------------------

    def force_cells(self, volts_mv):
        """Program every channel in mV, outputs on."""
        # self.sim.write("SOUR:VOLT:ALL " + ",".join(...))
        self._forced_mv = np.array(volts_mv, dtype=float)
        self._open[:] = False
        self._ship_mode = False

    def sim_readback_mv(self):
        """Simulator's own per-channel readback: the truth, not the setpoint."""
        return (self._forced_mv + self._rng.normal(0.0, 0.3, self.cell_count)).round(1).tolist()

    def open_channel(self, channel):
        """Open the output relay of one channel (1-based): simulates a broken sense wire."""
        self._open[channel - 1] = True

    def close_channel(self, channel):
        self._open[channel - 1] = False

    def sim_channel_current_ma(self, channel):
        """Current sourced by one channel on the 500 mA range (1-based)."""
        i = channel - 1
        if self._balancing[i]:
            return round(self.bleed_ma * (1.0 + self._rng.normal(0.0, 0.01)), 2)
        return round(self._rng.normal(0.0, 0.02), 2)

    def sim_total_current_ua(self):
        """Sum of channel currents on the 250 uA range: the DUT's quiescent draw."""
        per_ch = 1.4 if self._ship_mode else 38.0
        return round(per_ch * self.cell_count + self._rng.normal(0.0, 0.8), 1)

    def outputs_off(self):
        self._forced_mv[:] = 0.0

    # --- DUT side --------------------------------------------------------

    def dut_identify(self):
        """Identity block over UART: firmware, AFE, cell count, config CRC."""
        return {"firmware": "2.4.1", "afe": "BQ76952", "afe_die_rev": "B1",
                "cell_count": self.cell_count, "config_crc": "0x3A7F"}

    def dut_read_cells_mv(self):
        """Per-channel cell voltage as the DUT reports it. An open sense line
        floats toward the neighbours' midpoint and is flagged separately."""
        v = self._forced_mv * self._gain + self._offset_mv
        v = v + self._rng.normal(0.0, 0.2, self.cell_count)
        # Balancing current through the tap path drops the voltage the AFE sees.
        v = v - self._balancing * self.bleed_ma * self._tap_mohm / 1000.0
        for i in np.where(self._open)[0]:
            lo = self._forced_mv[i - 1] if i > 0 else 0.0
            hi = self._forced_mv[i + 1] if i + 1 < self.cell_count else self._forced_mv[i]
            v[i] = 0.5 * (lo + hi) + self._rng.normal(0.0, 15.0)
        return v.round(1).tolist()

    def dut_read_faults(self):
        """Fault registers decoded: lists of 1-based channels per fault class."""
        open_wire = (np.where(self._open)[0] + 1).tolist()
        return {"open_wire": open_wire, "ov": [], "uv": []}

    def dut_balance(self, channel, enable):
        """Command the bleed path of one channel (1-based) on or off."""
        self._balancing[channel - 1] = bool(enable)

    def dut_ship_mode(self):
        self._balancing[:] = False
        self._ship_mode = True
        return True

    def __del__(self):
        print("Outputs off, bench released")
