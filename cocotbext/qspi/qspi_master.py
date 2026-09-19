"""QSPI master: nibble-level bus driving."""

from cocotb.triggers import RisingEdge, FallingEdge

from .qspi_bus import QspiBus
from .qspi_config import QspiConfig


class QspiMaster:
    """Drives a :class:`QspiBus` as the master.

    The slave samples QSPI_IO on the rising edge of QSPI_CLK, so the master
    changes it on the falling edge and reads slave-driven data there too --
    sampling mid-bit rather than on the edge that changes it.
    """

    def __init__(self, bus: QspiBus, config: QspiConfig = None):
        self.bus = bus
        self.config = config or QspiConfig()

    async def start_transaction(self):
        """Assert chip select, aligned to a falling edge."""
        await FallingEdge(self.bus.clk)
        self.bus.cs.value = 0 if self.config.cs_active_low else 1
        self.bus.io_oe.value = 1

    async def end_transaction(self):
        """Release the bus and deassert chip select."""
        await FallingEdge(self.bus.clk)
        self.bus.io_oe.value = 0
        self.bus.cs.value = 1 if self.config.cs_active_low else 0

    async def send_nibble(self, nibble: int):
        self.bus.io_out.value = nibble & 0xF
        self.bus.io_oe.value = 1
        await RisingEdge(self.bus.clk)   # slave latches here
        await FallingEdge(self.bus.clk)  # safe point to change the data

    async def send_byte(self, byte: int):
        """Send one byte, most-significant nibble first."""
        await self.send_nibble((byte >> 4) & 0xF)
        await self.send_nibble(byte & 0xF)

    async def release_bus(self):
        """Stop driving QSPI_IO so the slave can drive it."""
        self.bus.io_oe.value = 0

    async def recv_nibble(self) -> int:
        """Read one slave-driven nibble, sampling mid-bit."""
        value = self.bus.io.value
        nibble = int(value)
        await FallingEdge(self.bus.clk)
        return nibble

    async def recv_byte(self) -> int:
        """Read one byte, most-significant nibble first."""
        high = await self.recv_nibble()
        low = await self.recv_nibble()
        return ((high & 0xF) << 4) | (low & 0xF)
