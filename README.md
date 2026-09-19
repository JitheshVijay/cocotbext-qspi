# cocotbext-qspi

A [cocotb](https://www.cocotb.org/) extension for driving quad-SPI flash
devices, plus a synthesisable QSPI flash slave model to test against.

Requires **cocotb 2.0+** and a simulator; the tests run on Icarus Verilog.

## Protocol

A transaction is framed by `QSPI_CS` (active low). Four bits move per rising
edge of `QSPI_CLK` on `QSPI_IO[3:0]`, most-significant nibble first, so each
byte takes two clocks.

| Operation | Sequence | Clocks |
|---|---|---|
| Page program | `0x02` \| address \| data | 6 |
| Read | `0x03` \| address \| dummy \| *data* | 7 |
| Sector erase | `0x20` \| address | 4 |

The slave drives `QSPI_IO` only during a read's data phase. The dummy clock
after the address gives the master a full cycle to release the bus before the
slave starts driving, so the two never contend — real QSPI parts insert dummy
cycles for the same reason.

Memory powers up erased (`0xFF`).

## Usage

```python
import cocotb
from cocotb.clock import Clock
from cocotbext.qspi import QspiFlash

@cocotb.test()
async def test_round_trip(dut):
    cocotb.start_soon(Clock(dut.QSPI_CLK, 20, units="ns").start())

    flash = QspiFlash(dut)
    await flash.initialize()

    await flash.write(0x01, 0xA5)
    assert await flash.read(0x01) == 0xA5

    await flash.erase(0x01)
    assert await flash.read(0x01) == 0xFF
```

## Bus signals

`QspiBus.from_entity(dut)` picks up `QSPI_CLK`, `QSPI_CS` and `QSPI_IO`, plus
`io_out` and `io_oe`.

A simulator will not let the testbench drive an `inout` net directly, so the
top level splits the master's half of `QSPI_IO` into a driven value (`io_out`)
and an output enable (`io_oe`); dropping `io_oe` hands the bus to the flash:

```verilog
wire [3:0] QSPI_IO;
assign QSPI_IO = io_oe ? io_out : 4'bzzzz;
```

See `verilog/qspi_flash_test.v`.

## Layout

| Path | Contents |
|---|---|
| `cocotbext/qspi/qspi_flash.py` | `QspiFlash` — write / read / erase |
| `cocotbext/qspi/qspi_master.py` | `QspiMaster` — nibble and byte level bus driving |
| `cocotbext/qspi/qspi_slave.py` | `QspiSlave` — passive bus monitor |
| `cocotbext/qspi/qspi_bus.py` | `QspiBus` — signal bundle |
| `cocotbext/qspi/qspi_config.py` | `QspiConfig` — width, polarity, lane count |
| `verilog/qspi_flash.v` | QSPI flash slave model |
| `verilog/qspi_flash_test.v` | cocotb top level with the tri-state split |

## Running the tests

```
pip install cocotb pytest
make -C tests
```

```
** TESTS=6 PASS=6 FAIL=0 SKIP=0 **
```
