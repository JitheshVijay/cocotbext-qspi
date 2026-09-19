// Top level for the cocotb testbench.
//
// cocotb cannot drive an inout net directly, so the master's half of the bus
// is split into a value (io_out) and a per-lane output enable (io_oe).
// Per-lane matters: in single-lane mode the master drives io0 while the
// device answers on io1, so one bus-wide enable would collide.
//
// csb is deliberately uninitialised -- the model frames on chip-select
// edges, and an initialiser here would race cocotb's first write at time 0.

`timescale 1ns/1ps

module qspi_flash_test;

    reg       csb;
    reg       clk = 1'b0;
    reg [3:0] io_out;
    reg [3:0] io_oe;

    wire [3:0] io;

    assign io[0] = io_oe[0] ? io_out[0] : 1'bz;
    assign io[1] = io_oe[1] ? io_out[1] : 1'bz;
    assign io[2] = io_oe[2] ? io_out[2] : 1'bz;
    assign io[3] = io_oe[3] ? io_out[3] : 1'bz;

    qspi_flash dut (
        .clk (clk),
        .csb (csb),
        .io  (io)
    );

endmodule
