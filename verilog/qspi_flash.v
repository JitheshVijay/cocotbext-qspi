// Quad-SPI flash slave model.
//
// A transaction is framed by QSPI_CS (active low). Four bits move per rising
// edge of QSPI_CLK on QSPI_IO, most-significant nibble first, so every byte
// takes two clocks:
//
//   write   0x02 | addr | data              6 clocks
//   read    0x03 | addr | dummy | <data>    7 clocks, slave drives the data
//   erase   0x20 | addr                     4 clocks
//
// The slave drives QSPI_IO only during a read's data phase. The dummy clock
// after the address gives the master a full cycle to release the bus before
// the slave starts driving it, so the two never contend -- real QSPI parts
// use dummy cycles for the same reason.
//
// Memory powers up erased (0xFF), as flash does.

`timescale 1ns/1ps

module qspi_flash #(
    parameter MEM_DEPTH = 256
)(
    input  wire       QSPI_CLK,
    input  wire       QSPI_CS,    // active low chip select
    inout  wire [3:0] QSPI_IO,
    input  wire       reset_n
);

    localparam [7:0] CMD_WRITE = 8'h02;
    localparam [7:0] CMD_READ  = 8'h03;
    localparam [7:0] CMD_ERASE = 8'h20;

    localparam [2:0] S_CMD   = 3'd0,
                     S_ADDR  = 3'd1,
                     S_WDATA = 3'd2,
                     S_DUMMY = 3'd3,
                     S_RDATA = 3'd4,
                     S_DONE  = 3'd5;

    reg [7:0] memory [0:MEM_DEPTH-1];
    reg [2:0] state;
    reg       nib;              // 0 = high nibble, 1 = low nibble
    reg [7:0] cmd, addr, rdata, shreg;

    // Byte as it stands once this clock's nibble is shifted in.
    wire [7:0] shifted = {shreg[3:0], QSPI_IO};

    integer i;
    initial begin
        for (i = 0; i < MEM_DEPTH; i = i + 1) memory[i] = 8'hFF;
        state = S_CMD;
        nib   = 1'b0;
        shreg = 8'h00;
    end

    // Only ever drive the bus while returning read data.
    assign QSPI_IO = (state == S_RDATA && !QSPI_CS)
                     ? (nib ? rdata[3:0] : rdata[7:4])
                     : 4'bzzzz;

    always @(posedge QSPI_CLK or negedge reset_n or posedge QSPI_CS) begin
        if (!reset_n) begin
            state <= S_CMD;
            nib   <= 1'b0;
            shreg <= 8'h00;
        end else if (QSPI_CS) begin
            // Deasserting chip select ends the transaction.
            state <= S_CMD;
            nib   <= 1'b0;
            shreg <= 8'h00;
        end else begin
            shreg <= shifted;
            case (state)
                S_CMD: begin
                    nib <= ~nib;
                    if (nib) begin
                        cmd   <= shifted;
                        state <= S_ADDR;
                    end
                end

                S_ADDR: begin
                    nib <= ~nib;
                    if (nib) begin
                        addr <= shifted;
                        case (cmd)
                            CMD_WRITE: state <= S_WDATA;
                            CMD_READ: begin
                                rdata <= memory[shifted];
                                state <= S_DUMMY;
                            end
                            CMD_ERASE: begin
                                memory[shifted] <= 8'hFF;
                                state <= S_DONE;
                            end
                            default: state <= S_DONE;
                        endcase
                    end
                end

                S_WDATA: begin
                    nib <= ~nib;
                    if (nib) begin
                        memory[addr] <= shifted;
                        state        <= S_DONE;
                    end
                end

                // One turnaround clock; the master releases QSPI_IO here.
                S_DUMMY: state <= S_RDATA;

                S_RDATA: begin
                    nib <= ~nib;
                    if (nib) state <= S_DONE;
                end

                default: ; // S_DONE: idle until chip select rises
            endcase
        end
    end

endmodule
