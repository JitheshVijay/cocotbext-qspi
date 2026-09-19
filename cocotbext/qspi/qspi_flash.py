"""High-level driver for the QSPI flash model."""

from cocotb.triggers import FallingEdge, RisingEdge, Timer

from .qspi_bus import QspiBus
from .qspi_config import QspiConfig
from .qspi_master import QspiMaster

CMD_WRITE = 0x02
CMD_READ = 0x03
CMD_ERASE = 0x20


class QspiFlash:
    """Page-program / read / erase against ``qspi_flash.v``.

    Each operation is one chip-select framed transaction:

    ==========  ==========================================
    write       ``0x02`` | address | data
    read        ``0x03`` | address | dummy clock | data
    erase       ``0x20`` | address
    ==========  ==========================================
    """

    def __init__(self, dut, bus: QspiBus = None, config: QspiConfig = None):
        self.dut = dut
        self.bus = bus or QspiBus.from_entity(dut)
        self.config = config or QspiConfig()
        self.master = QspiMaster(self.bus, self.config)

    async def initialize(self):
        """Pulse reset and leave the bus idle."""
        self.bus.cs.value = 1
        self.bus.io_oe.value = 0
        self.bus.io_out.value = 0
        self.dut.reset_n.value = 0
        await Timer(20, units="ns")
        self.dut.reset_n.value = 1
        await RisingEdge(self.bus.clk)

    async def write(self, address: int, data: int):
        """Program one byte at ``address``."""
        await self.master.start_transaction()
        await self.master.send_byte(CMD_WRITE)
        await self.master.send_byte(address & 0xFF)
        await self.master.send_byte(data & 0xFF)
        await self.master.end_transaction()

    async def read(self, address: int) -> int:
        """Read the byte at ``address``."""
        await self.master.start_transaction()
        await self.master.send_byte(CMD_READ)
        await self.master.send_byte(address & 0xFF)

        # Release during the dummy clock so master and slave never both drive.
        await self.master.release_bus()
        await RisingEdge(self.bus.clk)
        await FallingEdge(self.bus.clk)

        value = await self.master.recv_byte()
        await self.master.end_transaction()
        return value

    async def erase(self, address: int):
        """Erase ``address`` back to 0xFF."""
        await self.master.start_transaction()
        await self.master.send_byte(CMD_ERASE)
        await self.master.send_byte(address & 0xFF)
        await self.master.end_transaction()
