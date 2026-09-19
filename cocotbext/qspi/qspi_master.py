"""Bus-level QSPI master.

Timing is SPI mode 0, which is what flash parts use: the master launches
data while the clock is low and the device samples it on the rising edge;
the device launches its data while the clock is low and the master samples
on the rising edge. Nothing is ever read on the edge that changes it.

Every transfer method assumes the clock is **low on entry and leaves it
low on exit**, so transfers chain without a gap. Waiting for a falling edge
at the start of each one instead would let the rising edge in between clock
an undriven bit into the device, losing the first bit of every byte.

Lane count is per phase, not per transaction. A real quad-I/O read sends its
command on a single lane and only widens for the address, mode byte and
data, so every method takes its own ``lanes``.
"""

from cocotb.triggers import FallingEdge, RisingEdge


class QspiMaster:
    def __init__(self, bus, cs_active_low: bool = True):
        self.bus = bus
        self.cs_active_low = cs_active_low

    # ── framing ──────────────────────────────────────────────────────

    async def start(self):
        """Assert chip select, leaving the clock low and ready to transfer."""
        await FallingEdge(self.bus.clk)
        self.bus.cs.value = 0 if self.cs_active_low else 1

    async def stop(self):
        """Release the bus and deassert chip select."""
        self.bus.io_oe.value = 0
        self.bus.cs.value = 1 if self.cs_active_low else 0
        await FallingEdge(self.bus.clk)

    # ── driving ──────────────────────────────────────────────────────

    async def send_byte(self, byte: int, lanes: int = 1):
        """Send one byte most-significant bits first, ``lanes`` bits a clock."""
        if lanes not in (1, 2, 4):
            raise ValueError(f"lanes must be 1, 2 or 4, not {lanes!r}")
        mask = (1 << lanes) - 1
        for shift in range(8 - lanes, -1, -lanes):
            # Already in a low phase: drive now, let the rising edge sample it.
            self.bus.io_out.value = (byte >> shift) & mask
            # Only the lanes actually carrying data are driven; in single-lane
            # mode io1 belongs to the device.
            self.bus.io_oe.value = mask
            await RisingEdge(self.bus.clk)
            await FallingEdge(self.bus.clk)

    async def send_address(self, address: int, lanes: int = 1, width: int = 24):
        """Send an address, most-significant byte first."""
        for shift in range(width - 8, -1, -8):
            await self.send_byte((address >> shift) & 0xFF, lanes)

    # ── turnaround and receiving ─────────────────────────────────────

    def release(self):
        """Stop driving the bus so the device can."""
        self.bus.io_oe.value = 0

    async def dummy_cycles(self, count: int):
        """Clock ``count`` cycles with the bus released.

        Quad and dual reads need these between the address and the data so
        the device has time to turn the bus around.
        """
        self.release()
        for _ in range(count):
            await RisingEdge(self.bus.clk)
            await FallingEdge(self.bus.clk)

    def _lane_bit(self, lane: int) -> int:
        """Read one lane of the bus.

        Undriven lanes float, so the bus as a whole is rarely a clean integer
        and cannot be converted in one go -- read only the lane that carries
        data. Bit strings are most-significant first, so lane N is N places
        from the right.
        """
        bits = str(self.bus.io.value)
        bit = bits[-1 - lane]
        if bit not in "01":
            raise ValueError(
                f"io[{lane}] is '{bit}', not 0 or 1 (bus = {bits}). The device "
                f"is not driving it -- check the dummy cycle count and that "
                f"the master released the bus."
            )
        return int(bit)

    async def recv_byte(self, lanes: int = 1) -> int:
        """Read one byte the device is driving, sampling on rising edges.

        In single-lane mode the device answers on io1 (MISO); wider modes use
        the low ``lanes`` lines, most-significant first.
        """
        if lanes not in (1, 2, 4):
            raise ValueError(f"lanes must be 1, 2 or 4, not {lanes!r}")
        self.release()
        byte = 0
        for _ in range(8 // lanes):
            await RisingEdge(self.bus.clk)
            if lanes == 1:
                byte = (byte << 1) | self._lane_bit(1)   # io1 is MISO
            else:
                nibble = 0
                for lane in range(lanes - 1, -1, -1):
                    nibble = (nibble << 1) | self._lane_bit(lane)
                byte = (byte << lanes) | nibble
            await FallingEdge(self.bus.clk)
        return byte

    async def recv_bytes(self, count: int, lanes: int = 1) -> list:
        return [await self.recv_byte(lanes) for _ in range(count)]
