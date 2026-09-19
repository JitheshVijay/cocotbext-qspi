# Changelog

## 0.2.0

First public release.

QSPI flash verification for cocotb: a bus driver, a device-level API over
the JEDEC command set, and a NOR flash model to test against.

- `QspiFlash` — write enable latch, status register with WIP/WEL polling,
  page program, 4 KB sector erase, JEDEC id, deep power-down, software
  reset.
- `QspiMaster` — byte transfers at 1, 2 or 4 lanes, SPI mode 0 timing.
- `verilog/qspi_flash.v` — a NOR flash model where programming clears bits
  only, so a byte must be erased before it can be rewritten, and program and
  erase hold WIP for a simulated duration rather than completing instantly.
- The models ship inside the package; `verilog_dir()` locates them.
- Requires cocotb 2.0+.

Two test suites. The device suite drives our own model; the interop suite
drives [PicoSoC's `spiflash.v`](https://github.com/YosysHQ/picorv32), which
this project did not write. The split is deliberate — testing only against
our own model proves the driver and the model agree, not that either is
right.

Earlier revisions of this code existed but were never usable: the RTL,
driver and tests disagreed with each other and nothing had run. 0.2.0 is the
first version that works.
