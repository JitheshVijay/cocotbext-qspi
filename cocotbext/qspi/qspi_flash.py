"""Device-level driver for a QSPI NOR flash."""

from cocotb.triggers import RisingEdge

from .qspi_bus import QspiBus
from .qspi_master import QspiMaster

# JEDEC opcodes. The opcode itself is always single-lane; only the address,
# mode byte and data widen.
CMD_WREN = 0x06   # write enable
CMD_WRDI = 0x04   # write disable
CMD_RDSR = 0x05   # read status register
CMD_RDID = 0x9F   # read JEDEC id
CMD_RDP = 0xAB    # release from deep power-down
CMD_DP = 0xB9     # deep power-down
CMD_READ = 0x03   # read data
CMD_QIOR2 = 0xBB  # fast read dual I/O
CMD_QIOR4 = 0xEB  # fast read quad I/O
CMD_PP = 0x02     # page program
CMD_SE = 0x20     # sector erase
CMD_RSTEN = 0x66  # reset enable
CMD_RST = 0x99    # reset memory

STATUS_WIP = 0x01  # write in progress
STATUS_WEL = 0x02  # write enable latch

# Lanes used for the address/mode/data phases of each read opcode.
READ_LANES = {CMD_READ: 1, CMD_QIOR2: 2, CMD_QIOR4: 4}


class QspiFlash:
    """Drives a QSPI NOR flash the way a real controller does.

    Programming clears bits only, so a byte must be erased before it can be
    rewritten -- :meth:`program` will not silently turn a 0 back into a 1.
    Program and erase assert WIP; :meth:`wait_ready` polls the status
    register rather than assuming a fixed delay.
    """

    #: Dummy cycles between the mode byte and read data. Matches the
    #: model's DUMMY parameter; real parts vary, so it is configurable.
    dummy_cycles = 8

    def __init__(self, dut, bus: QspiBus = None, dummy_cycles: int = None):
        self.dut = dut
        self.bus = bus or QspiBus.from_entity(dut)
        self.master = QspiMaster(self.bus)
        if dummy_cycles is not None:
            self.dummy_cycles = dummy_cycles

    async def initialize(self):
        """Put the bus in a known state and frame the device.

        The model sets up its framing on a chip-select edge, so drive one
        before the first transaction rather than relying on initial values.
        """
        self.bus.io_oe.value = 0
        self.bus.io_out.value = 0
        self.bus.cs.value = 1
        await RisingEdge(self.bus.clk)
        self.bus.cs.value = 0
        await RisingEdge(self.bus.clk)
        self.bus.cs.value = 1
        await RisingEdge(self.bus.clk)
        await self.reset()
        await self.release_power_down()

    async def reset(self):
        """Software-reset the device: RSTEN then RST.

        Without this a test inherits whatever state the previous one left --
        the write enable latch in particular. Nothing depends on it today,
        but only because the tests happen to use separate addresses.
        """
        await self._command(CMD_RSTEN)
        await self._command(CMD_RST)

    # ── simple commands ──────────────────────────────────────────────

    async def _command(self, opcode: int):
        await self.master.start()
        await self.master.send_byte(opcode, lanes=1)
        await self.master.stop()

    async def release_power_down(self):
        await self._command(CMD_RDP)

    async def power_down(self):
        await self._command(CMD_DP)

    async def write_enable(self):
        await self._command(CMD_WREN)

    async def write_disable(self):
        await self._command(CMD_WRDI)

    # ── status ───────────────────────────────────────────────────────

    async def read_status(self) -> int:
        await self.master.start()
        await self.master.send_byte(CMD_RDSR, lanes=1)
        status = await self.master.recv_byte(lanes=1)
        await self.master.stop()
        return status

    async def read_id(self) -> list:
        """Read the three JEDEC id bytes."""
        await self.master.start()
        await self.master.send_byte(CMD_RDID, lanes=1)
        ident = await self.master.recv_bytes(3, lanes=1)
        await self.master.stop()
        return ident

    async def is_busy(self) -> bool:
        return bool(await self.read_status() & STATUS_WIP)

    async def wait_ready(self, timeout_polls: int = 1000):
        """Poll the status register until WIP clears.

        This is how a controller learns a program or erase finished; assuming
        a fixed delay instead is what hides real timing bugs.
        """
        for _ in range(timeout_polls):
            if not await self.is_busy():
                return
        raise TimeoutError(
            f"WIP still set after {timeout_polls} status polls"
        )

    # ── reads ────────────────────────────────────────────────────────

    async def read(self, address: int, length: int = 1, opcode: int = CMD_READ) -> list:
        """Read ``length`` bytes starting at ``address``.

        ``opcode`` picks the width: 0x03 single, 0xBB dual I/O, 0xEB quad
        I/O. The wider ones send a mode byte and dummy cycles after the
        address.
        """
        try:
            lanes = READ_LANES[opcode]
        except KeyError:
            raise ValueError(f"{opcode:#04x} is not a read opcode") from None

        await self.master.start()
        await self.master.send_byte(opcode, lanes=1)
        await self.master.send_address(address, lanes=lanes)
        if lanes > 1:
            # Mode byte: 0xA5 would arm continuous-read (XIP) on a real part,
            # so send 0x00 to keep each transaction self-contained.
            await self.master.send_byte(0x00, lanes=lanes)
            await self.master.dummy_cycles(self.dummy_cycles)
        data = await self.master.recv_bytes(length, lanes=lanes)
        await self.master.stop()
        return data

    async def read_byte(self, address: int, opcode: int = CMD_READ) -> int:
        return (await self.read(address, 1, opcode))[0]

    # ── writes ───────────────────────────────────────────────────────

    async def program(self, address: int, data, wait: bool = True):
        """Page program. Sets WEL first, as the device requires.

        NOR programming only clears bits, so program into erased space.
        """
        if isinstance(data, int):
            data = [data]

        await self.write_enable()
        await self.master.start()
        await self.master.send_byte(CMD_PP, lanes=1)
        await self.master.send_address(address, lanes=1)
        for byte in data:
            await self.master.send_byte(byte & 0xFF, lanes=1)
        await self.master.stop()

        if wait:
            await self.wait_ready()

    async def erase_sector(self, address: int, wait: bool = True):
        """Erase the 4 KB sector containing ``address`` back to 0xFF."""
        await self.write_enable()
        await self.master.start()
        await self.master.send_byte(CMD_SE, lanes=1)
        await self.master.send_address(address, lanes=1)
        await self.master.stop()

        if wait:
            await self.wait_ready()
