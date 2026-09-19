"""Functional tests for the QSPI NOR flash model and the cocotbext-qspi driver."""

import cocotb
from cocotb.clock import Clock

from cocotbext.qspi import (
    QspiFlash, CMD_READ, CMD_QIOR2, CMD_QIOR4, STATUS_WEL, STATUS_WIP,
)

READ_OPCODES = [CMD_READ, CMD_QIOR2, CMD_QIOR4]
OPCODE_NAMES = {CMD_READ: "read", CMD_QIOR2: "dual I/O", CMD_QIOR4: "quad I/O"}


async def setup(dut):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    flash = QspiFlash(dut)
    await flash.initialize()
    return flash


@cocotb.test()
async def test_jedec_id(dut):
    """The device identifies itself."""
    flash = await setup(dut)
    assert await flash.read_id() == [0xEF, 0x40, 0x18]


@cocotb.test()
async def test_erased_memory_reads_ff(dut):
    """Flash powers up erased."""
    flash = await setup(dut)
    assert await flash.read(0x000000, 4) == [0xFF] * 4


@cocotb.test()
async def test_write_enable_latch(dut):
    """WREN sets WEL and WRDI clears it."""
    flash = await setup(dut)
    assert not await flash.read_status() & STATUS_WEL

    await flash.write_enable()
    assert await flash.read_status() & STATUS_WEL

    await flash.write_disable()
    assert not await flash.read_status() & STATUS_WEL


@cocotb.test()
async def test_program_requires_write_enable(dut):
    """A program with no WEL is ignored, as the device requires."""
    flash = await setup(dut)

    # Bypass program()'s automatic WREN to send a bare page program.
    await flash.master.start()
    await flash.master.send_byte(0x02, lanes=1)
    await flash.master.send_address(0x000000, lanes=1)
    await flash.master.send_byte(0xA5, lanes=1)
    await flash.master.stop()

    assert await flash.read_byte(0x000000) == 0xFF, "programmed without WEL"


@cocotb.test()
async def test_program_then_read(dut):
    """A programmed byte reads back."""
    flash = await setup(dut)
    await flash.program(0x000010, 0xA5)
    assert await flash.read_byte(0x000010) == 0xA5


@cocotb.test()
async def test_program_clears_bits_only(dut):
    """NOR programming can clear bits but never set them."""
    flash = await setup(dut)
    await flash.program(0x000020, 0xF0)
    assert await flash.read_byte(0x000020) == 0xF0

    # 0x0F shares no set bits with 0xF0, so the result is 0x00 -- not 0x0F.
    await flash.program(0x000020, 0x0F)
    assert await flash.read_byte(0x000020) == 0x00

    # Only an erase restores the bits.
    await flash.erase_sector(0x000020)
    assert await flash.read_byte(0x000020) == 0xFF


@cocotb.test()
async def test_wip_is_asserted_during_program(dut):
    """The device reports busy, and WEL is consumed by the operation."""
    flash = await setup(dut)

    await flash.write_enable()
    await flash.master.start()
    await flash.master.send_byte(0x02, lanes=1)
    await flash.master.send_address(0x000030, lanes=1)
    await flash.master.send_byte(0x5A, lanes=1)
    await flash.master.stop()

    status = await flash.read_status()
    assert status & STATUS_WIP, f"WIP not set after program (status {status:#04x})"

    await flash.wait_ready()
    status = await flash.read_status()
    assert not status & STATUS_WIP
    assert not status & STATUS_WEL, "WEL should be consumed by the program"
    assert await flash.read_byte(0x000030) == 0x5A


@cocotb.test()
async def test_page_program_multiple_bytes(dut):
    """A page program writes a run of bytes."""
    flash = await setup(dut)
    payload = [0x11, 0x22, 0x33, 0x44, 0x55]
    await flash.program(0x000040, payload)
    assert await flash.read(0x000040, len(payload)) == payload


@cocotb.test()
async def test_read_widths_agree(dut):
    """Single, dual I/O and quad I/O return the same bytes."""
    flash = await setup(dut)
    payload = [0x00, 0x0F, 0xF0, 0xA5, 0x5A, 0x81]
    await flash.program(0x000050, payload)

    for opcode in READ_OPCODES:
        got = await flash.read(0x000050, len(payload), opcode=opcode)
        assert got == payload, (
            f"{OPCODE_NAMES[opcode]}: {[hex(b) for b in got]}"
        )


@cocotb.test()
async def test_sector_erase_spans_the_sector(dut):
    """Erase clears its whole 4 KB sector and leaves the next one alone."""
    flash = await setup(dut)
    await flash.program(0x000000, 0x11)
    await flash.program(0x000FFF, 0x22)
    await flash.program(0x001000, 0x33)   # next sector

    await flash.erase_sector(0x000000)

    assert await flash.read_byte(0x000000) == 0xFF
    assert await flash.read_byte(0x000FFF) == 0xFF
    assert await flash.read_byte(0x001000) == 0x33, "erase crossed the sector"


@cocotb.test()
async def test_reads_auto_increment(dut):
    """A read streams consecutive addresses."""
    flash = await setup(dut)
    payload = [0xDE, 0xAD, 0xBE, 0xEF]
    await flash.program(0x000060, payload)
    assert await flash.read(0x000060, 4) == payload


@cocotb.test()
async def test_software_reset_clears_the_write_enable_latch(dut):
    """RSTEN then RST drops WEL, so a test cannot inherit an armed device."""
    flash = await setup(dut)

    await flash.write_enable()
    assert await flash.read_status() & STATUS_WEL

    await flash.reset()
    assert not await flash.read_status() & STATUS_WEL


@cocotb.test()
async def test_reset_needs_reset_enable_first(dut):
    """RST on its own does nothing; RSTEN has to immediately precede it.

    A command in between cancels the arming, which is what the real
    sequence requires and why it exists -- a stray 0x99 should not reset a
    device mid-operation.
    """
    flash = await setup(dut)
    await flash.write_enable()
    assert await flash.read_status() & STATUS_WEL

    # RST alone, with no RSTEN: ignored.
    await flash._command(0x99)
    assert await flash.read_status() & STATUS_WEL, "bare RST reset the device"

    # RSTEN, then something else, then RST: the arming is cancelled.
    await flash._command(0x66)
    await flash.read_status()
    await flash._command(0x99)
    assert await flash.read_status() & STATUS_WEL, \
        "RST honoured despite an intervening command"

    # The proper pair works.
    await flash.reset()
    assert not await flash.read_status() & STATUS_WEL
