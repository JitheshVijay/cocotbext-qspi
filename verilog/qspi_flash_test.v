// Top level for the cocotb testbench.
//
// cocotb acts as the QSPI master. It cannot drive an inout net directly, so
// the master's side of QSPI_IO is split into a value (io_out) and an output
// enable (io_oe); releasing io_oe hands the bus to the flash for read data.

`timescale 1ns/1ps

module qspi_flash_test;

    reg        QSPI_CLK = 1'b0;
    reg        QSPI_CS  = 1'b1;   // active low, starts deasserted
    reg        reset_n  = 1'b0;
    reg [3:0]  io_out   = 4'h0;
    reg        io_oe    = 1'b0;

    wire [3:0] QSPI_IO;

    assign QSPI_IO = io_oe ? io_out : 4'bzzzz;

    qspi_flash dut (
        .QSPI_CLK (QSPI_CLK),
        .QSPI_CS  (QSPI_CS),
        .QSPI_IO  (QSPI_IO),
        .reset_n  (reset_n)
    );

endmodule
