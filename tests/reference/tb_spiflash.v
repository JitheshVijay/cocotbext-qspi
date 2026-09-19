// Interop top level: cocotbext-qspi driving an independent flash model.
//
// The DUT here is spiflash.v from PicoSoC (Claire Xenia Wolf, ISC licence) --
// a model this project did not write. Driving it correctly is what shows the
// driver speaks real QSPI rather than only agreeing with our own slave.
//
// Each lane gets its own output enable: in single-lane mode the master drives
// io0 while the flash drives io1, so a single bus-wide enable will not do.

`timescale 1ns/1ps

module tb_spiflash;

    // Deliberately uninitialised: spiflash.v sets up its mode and counters
    // from a chip-select edge, and an initialiser here would race cocotb's
    // first write at time 0 -- the edge would be lost and the model would
    // never leave mode 0. The test drives csb high, low, high in simulation
    // time instead.
    reg       csb;             // active low chip select
    reg       clk = 1'b0;
    reg [3:0] io_out;
    reg [3:0] io_oe;           // per-lane output enable

    wire [3:0] io;

    assign io[0] = io_oe[0] ? io_out[0] : 1'bz;
    assign io[1] = io_oe[1] ? io_out[1] : 1'bz;
    assign io[2] = io_oe[2] ? io_out[2] : 1'bz;
    assign io[3] = io_oe[3] ? io_out[3] : 1'bz;

    spiflash flash (
        .csb (csb),
        .clk (clk),
        .io0 (io[0]),
        .io1 (io[1]),
        .io2 (io[2]),
        .io3 (io[3])
    );

endmodule
