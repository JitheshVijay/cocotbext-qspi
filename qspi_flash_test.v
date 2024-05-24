module qspi_flash_test;
    reg qspi_sclk;
    reg qspi_mosi;
    wire qspi_miso;
    reg qspi_cs;
    reg reset_n;
    reg clk;
    reg write_enable;
    reg read_enable;
    reg erase_enable;
    reg [7:0] data_in;
    reg [7:0] address;
    wire [7:0] data_out;

    // Instantiate the DUT
    qspi_flash dut (
        .qspi_sclk(qspi_sclk),
        .qspi_mosi(qspi_mosi),
        .qspi_miso(qspi_miso),
        .qspi_cs(qspi_cs),
        .reset_n(reset_n),
        .clk(clk),
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
        
        // Initialize signals
        qspi_sclk = 0;
        qspi_mosi = 0;
        qspi_cs = 1;
        reset_n = 0;
        clk = 0;
        write_enable = 0;
        read_enable = 0;
        erase_enable = 0;
        data_in = 0;
        address = 0;
        
        #10 reset_n = 1;  // Release reset after 10 time units
    end

    always #5 clk = ~clk;  // Generate clock with period of 10 time units
endmodule

