module qspi_flash (
    input wire qspi_sclk,
    input wire qspi_mosi,
    output wire qspi_miso,
    input wire qspi_cs,
    input wire reset_n,
    input wire clk,
    input wire write_enable,
    input wire read_enable,
    input wire erase_enable,
    input wire [7:0] data_in,
    input wire [7:0] address,
    output reg [7:0] data_out
);

reg [7:0] memory [0:255];

always @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
        data_out <= 8'hFF;  // Typical erased flash memory value
    end else begin
        if (write_enable) begin
            memory[address] <= data_in;
        end
        if (read_enable) begin
            data_out <= memory[address];
        end
        if (erase_enable) begin
            memory[address] <= 8'hFF;
        end
    end
end

endmodule
