"""Interop: drive PicoSoC's spiflash.v, a model this project did not write.

Passing here means the driver speaks real QSPI -- single-lane command phase,
24-bit address, mode byte, dummy cycles -- rather than only agreeing with our
own slave model.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

from cocotbext.qspi.qspi_bus import QspiBus
from cocotbext.qspi.qspi_master import QspiMaster

# Matches tests/reference/firmware.hex.
EXPECTED = [(0xA0 + i) & 0xFF for i in range(16)] + \
           [(i * 7 + 3) & 0xFF for i in range(240)]

CMD_RELEASE_POWER_DOWN = 0xAB
CMD_READ = 0x03
CMD_FAST_READ_DUAL_IO = 0xBB
CMD_FAST_READ_QUAD_IO = 0xEB

# spiflash.v uses `localparam integer latency = 8`.
DUMMY_CYCLES = 8


async def setup(dut):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    bus = QspiBus(clk=dut.clk, cs=dut.csb, io=dut.io,
                  io_out=dut.io_out, io_oe=dut.io_oe)
    master = QspiMaster(bus)

    dut.io_oe.value = 0
    dut.io_out.value = 0

    # spiflash.v initialises its mode and counters from a chip-select edge.
    # Drive it high, low, then high with time in between so the model starts
    # from a known state, as it would at power-on.
    dut.csb.value = 1
    await RisingEdge(dut.clk)
    dut.csb.value = 0
    await RisingEdge(dut.clk)
    dut.csb.value = 1
    await RisingEdge(dut.clk)

    # The model ignores every read until it is brought out of power-down.
    await master.start()
    await master.send_byte(CMD_RELEASE_POWER_DOWN, lanes=1)
    await master.stop()
    await RisingEdge(dut.clk)
    return master


@cocotb.test()
async def test_single_lane_read(dut):
    """0x03: command, address and data all on one lane, no dummy cycles."""
    master = await setup(dut)

    await master.start()
    await master.send_byte(CMD_READ, lanes=1)
    await master.send_address(0x000000, lanes=1)
    got = await master.recv_bytes(8, lanes=1)
    await master.stop()

    assert got == EXPECTED[:8], f"got {[hex(b) for b in got]}"


@cocotb.test()
async def test_single_lane_read_at_offset(dut):
    """The address actually selects where the read starts."""
    master = await setup(dut)

    await master.start()
    await master.send_byte(CMD_READ, lanes=1)
    await master.send_address(0x000010, lanes=1)
    got = await master.recv_bytes(8, lanes=1)
    await master.stop()

    assert got == EXPECTED[0x10:0x18], f"got {[hex(b) for b in got]}"


@cocotb.test()
async def test_dual_io_read(dut):
    """0xBB: single-lane command, then two lanes for address and data."""
    master = await setup(dut)

    await master.start()
    await master.send_byte(CMD_FAST_READ_DUAL_IO, lanes=1)
    await master.send_address(0x000000, lanes=2)
    await master.send_byte(0x00, lanes=2)        # mode byte; 0xA5 would arm XIP
    await master.dummy_cycles(DUMMY_CYCLES)
    got = await master.recv_bytes(8, lanes=2)
    await master.stop()

    assert got == EXPECTED[:8], f"got {[hex(b) for b in got]}"


@cocotb.test()
async def test_quad_io_read(dut):
    """0xEB: single-lane command, then four lanes for address and data."""
    master = await setup(dut)

    await master.start()
    await master.send_byte(CMD_FAST_READ_QUAD_IO, lanes=1)
    await master.send_address(0x000000, lanes=4)
    await master.send_byte(0x00, lanes=4)        # mode byte
    await master.dummy_cycles(DUMMY_CYCLES)
    got = await master.recv_bytes(8, lanes=4)
    await master.stop()

    assert got == EXPECTED[:8], f"got {[hex(b) for b in got]}"


@cocotb.test()
async def test_all_widths_agree(dut):
    """The same bytes come back whichever width they are read at."""
    master = await setup(dut)
    address = 0x000020

    await master.start()
    await master.send_byte(CMD_READ, lanes=1)
    await master.send_address(address, lanes=1)
    single = await master.recv_bytes(4, lanes=1)
    await master.stop()

    await master.start()
    await master.send_byte(CMD_FAST_READ_QUAD_IO, lanes=1)
    await master.send_address(address, lanes=4)
    await master.send_byte(0x00, lanes=4)
    await master.dummy_cycles(DUMMY_CYCLES)
    quad = await master.recv_bytes(4, lanes=4)
    await master.stop()

    assert single == quad == EXPECTED[0x20:0x24], f"{single} vs {quad}"
