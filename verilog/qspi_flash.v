module qspi_flash (
    input wire QSPI_CLK,        // QSPI serial clock input
    inout wire [3:0] QSPI_IO,   // QSPI data lines (0 to 3)
    input wire QSPI_CS,       // Chip select (active low)
    input wire QSPI_RST,      // Reset signal (active low)
    input wire clk,             // Clock input for internal logic
    input wire reset_n,         // Active-low reset input
    input wire write_enable,    // Write enable signal
    input wire read_enable,     // Read enable signal
    input wire erase_enable,    // Erase enable signal
    input wire [3:0] data_in,   // Data input for write operation
    input wire [7:0] address,   // Address input for memory access
    output reg [3:0] data_out   // Data output for read operation
);

    // Memory array to store data, 256 bytes in size
    reg [7:0] memory [0:255];
    reg [7:0] data_buffer;      // Buffer to handle bidirectional data lines

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            data_out <= 4'hF;  // Initialize data_out to 0xF on reset
        end else begin
            if (write_enable) begin
                memory[address][3:0] <= data_in; // Write lower nibble
                memory[address][7:4] <= data_in; // Write upper nibble
            end
            if (read_enable) begin
                data_out <= memory[address][3:0];   // Read lower nibble from memory
                data_out <= memory[address][7:4];   // Read upper nibble from memory
            end
            if (erase_enable) begin
                memory[address] <= 8'hFF;      // Erase data by writing 0xFF to memory at specified address
            end
        end
    end

    // Assign QSPI data lines based on operation mode
    assign QSPI_IO[0] = (write_enable || erase_enable) ? data_in[0] : 1'bz;
    assign QSPI_IO[1] = (write_enable || erase_enable) ? data_in[1] : 1'bz;
    assign QSPI_IO[2] = (write_enable || erase_enable) ? data_in[2] : 1'bz;
    assign QSPI_IO[3] = (write_enable || erase_enable) ? data_in[3] : 1'bz;

endmodule
