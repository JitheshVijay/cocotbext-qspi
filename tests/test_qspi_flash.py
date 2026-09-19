"""Functional tests for the QSPI flash model and the cocotbext-qspi driver."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

from cocotbext.qspi import QspiFlash


async def setup(dut):
    """Start the QSPI clock and reset the flash."""
    cocotb.start_soon(Clock(dut.QSPI_CLK, 20, units="ns").start())
    flash = QspiFlash(dut)
    await flash.initialize()
    return flash


@cocotb.test()
async def test_write_then_read(dut):
    """A programmed byte reads back unchanged."""
    flash = await setup(dut)
    await flash.write(0x01, 0xA5)
    assert await flash.read(0x01) == 0xA5


@cocotb.test()
async def test_erase_restores_ff(dut):
    """Erasing returns the byte to 0xFF."""
    flash = await setup(dut)
    await flash.write(0x01, 0x5A)
    assert await flash.read(0x01) == 0x5A
    await flash.erase(0x01)
    assert await flash.read(0x01) == 0xFF


@cocotb.test()
async def test_addresses_are_independent(dut):
    """Writing one address leaves its neighbours alone."""
    flash = await setup(dut)
    await flash.write(0x10, 0x11)
    await flash.write(0x11, 0x22)
    await flash.write(0x12, 0x33)
    assert await flash.read(0x10) == 0x11
    assert await flash.read(0x11) == 0x22
    assert await flash.read(0x12) == 0x33


@cocotb.test()
async def test_unwritten_memory_reads_erased(dut):
    """Flash powers up erased."""
    flash = await setup(dut)
    assert await flash.read(0x7F) == 0xFF


@cocotb.test()
async def test_byte_values_round_trip(dut):
    """Every nibble pattern survives the round trip."""
    flash = await setup(dut)
    for addr, value in enumerate([0x00, 0x0F, 0xF0, 0xFF, 0xA5, 0x5A, 0x81]):
        await flash.write(addr, value)
    for addr, value in enumerate([0x00, 0x0F, 0xF0, 0xFF, 0xA5, 0x5A, 0x81]):
        assert await flash.read(addr) == value, f"addr {addr:#04x}"


@cocotb.test()
async def test_overwrite(dut):
    """A second program to the same address takes effect."""
    flash = await setup(dut)
    await flash.write(0x20, 0x12)
    await flash.write(0x20, 0x34)
    assert await flash.read(0x20) == 0x34
