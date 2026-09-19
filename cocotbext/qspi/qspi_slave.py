"""Passive monitor for the QSPI bus."""

from cocotb.triggers import RisingEdge


class QspiSlave:
    """Observes nibbles on QSPI_IO without driving anything.

    Useful for checking what a master put on the wire; the flash model in
    ``verilog/qspi_flash.v`` is the active slave.
    """

    def __init__(self, bus, config=None):
        self.bus = bus
        self.config = config

    async def capture_nibble(self) -> int:
        await RisingEdge(self.bus.clk)
        return int(self.bus.io.value)

    async def capture_byte(self) -> int:
        high = await self.capture_nibble()
        low = await self.capture_nibble()
        return ((high & 0xF) << 4) | (low & 0xF)
