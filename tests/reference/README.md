# Third-party reference model

`spiflash.v` is **not** part of this project. It comes from
[PicoSoC](https://github.com/YosysHQ/picorv32) by Claire Xenia Wolf and is
used under the ISC licence reproduced at the top of the file.

It is here so `test_interop.py` can drive a flash model this project did not
write. Tests that only exercise our own `verilog/qspi_flash.v` prove the
driver and the model agree with each other; driving somebody else's model is
what shows the driver speaks real QSPI.

It found a genuine bug: the master was dropping the first bit of every byte,
and our own model had the same off-by-one assumption, so the closed loop
agreed with itself and the tests passed.

`firmware.hex` is generated known content that `spiflash.v` loads with
`$readmemh`.
