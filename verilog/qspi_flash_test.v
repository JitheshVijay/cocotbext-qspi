module qspi_flash_test;
    reg QSPI_CLK;             // QSPI serial clock
    wire [3:0] QSPI_IO;       // QSPI data lines (inout needs to be wire)
    reg QSPI_CS_b;            // QSPI chip select
    reg QSPI_RST_b;           // QSPI reset
    reg reset_n;              // Active-low reset signal
    reg clk;                  // Clock signal
    reg write_enable;         // Write enable signal
    reg read_enable;          // Read enable signal
    reg erase_enable;         // Erase enable signal
    reg [3:0] data_in;        // Data input for memory operations
    reg [7:0] address;        // Address input for memory operations
    wire [3:0] data_out;      // Data output from memory operations

    // Tri-state buffer for inout port QSPI_IO
    assign QSPI_IO = (write_enable || erase_enable) ? data_in : 4'bz;

    qspi_flash dut (
        .QSPI_CLK(QSPI_CLK),
        .QSPI_IO(QSPI_IO),
        .QSPI_CS_b(QSPI_CS_b),
        .QSPI_RST_b(QSPI_RST_b),
        .clk(clk),
        .reset_n(reset_n),
        .write_enable(write_enable),
        .read_enable(read_enable),
        .erase_enable(erase_enable),
        .data_in(data_in),
        .address(address),
        .data_out(data_out)
    );

    initial begin
        $dumpfile("waves.vcd");
        $dumpvars(0, qspi_flash_test);

        // Initial values
        QSPI_CLK = 0;
        QSPI_CS_b = 1;
        QSPI_RST_b = 0;
        clk = 0;
        reset_n = 0;
        write_enable = 0;
        read_enable = 0;
        erase_enable = 0;
        data_in = 0;
        address = 0;

        // Reset sequence
        #10 reset_n = 1;
        QSPI_RST_b = 1;

        // Test sequence example
        #20 write_enable = 1;
        data_in = 4'hA;
        address = 8'h00;
        #10 write_enable = 0;

        #20 read_enable = 1;
        address = 8'h00;
        #10 read_enable = 0;

        // Wait some time and finish
        #100 $finish;
    end

    always #5 clk = ~clk;

    // Generate QSPI clock
    always #10 QSPI_CLK = ~QSPI_CLK;

    // Display values during simulation
    always @(posedge clk) begin
        if (write_enable) $display("Writing data: %h to address: %h", data_in, address);
        if (read_enable) $display("Reading data: %h from address: %h", data_out, address);
    end

endmodule


