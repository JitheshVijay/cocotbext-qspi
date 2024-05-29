# QSPI Interface for Cocotb

QSPI simulation framework for cocotb.

## Documentation
To properly handle QSPI (Quad SPI), which involves four data lines (IO0, IO1, IO2, IO3), we need to update the module to include these lines and adjust the communication logic accordingly. Below is the revised Verilog module and testbench documentation to support QSPI with four data lines.

### Creating a custom cocotbext.qspi
Directory Structure of QSPI module:

```markdown
cocotbext/
    __init__.py
    qspi/
        __init__.py
        qspi_bus.py
        qspi_master.py
        qspi_slave.py
        qspi_config.py
```

cocotbext/__init__.py
```
# This file is empty
```
cocotbext/qspi/__init__.py

```
from .qspi_bus import QspiBus
from .qspi_master import QspiMaster
from .qspi_slave import QspiSlave
from .qspi_config import QspiConfig

__all__ = ["QspiBus", "QspiMaster", "QspiSlave", "QspiConfig"]
```
##### QspiBus 
This class will handle the initialization of the QSPI signals.

qspi_bus.py
```python
import cocotb
from cocotb.handle import SimHandle

class QspiBus:
    def __init__(self, sclk, cs, io0, io1, io2, io3):
        self.sclk = sclk    # Serial clock signal
        self.cs = cs        # Chip select signal
        self.io0 = io0      # Data line 0
        self.io1 = io1      # Data line 1
        self.io2 = io2      # Data line 2
        self.io3 = io3      # Data line 3

    @classmethod
    def from_prefix(cls, entity: SimHandle, prefix: str):
        # Retrieve signals based on prefix
        sclk = getattr(entity, f"{prefix}_sclk")
        cs = getattr(entity, f"{prefix}_cs")
        io0 = getattr(entity, f"{prefix}_io0")
        io1 = getattr(entity, f"{prefix}_io1")
        io2 = getattr(entity, f"{prefix}_io2")
        io3 = getattr(entity, f"{prefix}_io3")
        return cls(sclk, cs, io0, io1, io2, io3)

```
##### QspiConfig
This class will handle the QSPI configuration parameters.

 qspi_config.py
```python
class QspiConfig:
    def __init__(self, word_width, sclk_freq, cpol, cpha, cs_active_low, quad_mode=True):
        self.word_width = word_width  # Data width in bits
        self.sclk_freq = sclk_freq    # Serial clock frequency
        self.cpol = cpol              # Clock polarity
        self.cpha = cpha              # Clock phase
        self.cs_active_low = cs_active_low  # Chip select active low flag
        self.quad_mode = quad_mode    # Quad mode flag (default True)
```
##### QspiMaster and QspiSlave
This class will handle the QSPI operations.

qspi_master.py
```python
import cocotb
from cocotb.triggers import Timer, RisingEdge

class QspiMaster:
    def __init__(self, bus: QspiBus, config: QspiConfig):
        self.bus = bus    # QSPI bus signals
        self.config = config  # QSPI configuration

    async def write(self, data):
        await self._start_transaction()  # Start the transaction
        for byte in data:
            await self._write_byte(byte)  # Write each byte
        await self._end_transaction()  # End the transaction

    async def read(self, length):
        await self._start_transaction()  # Start the transaction
        data = [await self._read_byte() for _ in range(length)]  # Read bytes
        await self._end_transaction()  # End the transaction
        return data  # Return the read data

    async def _start_transaction(self):
        self.bus.cs.value = 0 if self.config.cs_active_low else 1  # Assert chip select
        await Timer(1, units='ns')  # Wait for 1 ns

    async def _end_transaction(self):
        self.bus.cs.value = 1 if self.config.cs_active_low else 0  # Deassert chip select
        await Timer(1, units='ns')  # Wait for 1 ns

    async def _write_byte(self, byte):
        for i in range(2):  # Two cycles for 8 bits, as each cycle writes 4 bits
            nibble = (byte >> (4 * (1 - i))) & 0xF  # Extract 4 bits (nibble)
            self.bus.io0.value = (nibble >> 0) & 1  # Set the value for io0
            self.bus.io1.value = (nibble >> 1) & 1  # Set the value for io1
            self.bus.io2.value = (nibble >> 2) & 1  # Set the value for io2
            self.bus.io3.value = (nibble >> 3) & 1  # Set the value for io3
            await RisingEdge(self.bus.sclk)
        await Timer(1, units='ns')

    async def _read_byte(self):
        byte = 0
        for i in range(2):  # Two cycles for 8 bits, as each cycle reads 4 bits
            await RisingEdge(self.bus.sclk)
            # Read 4 bits from the QSPI lines and combine them into a nibble
            nibble = (
                (int(self.bus.io3.value) << 3) |
                (int(self.bus.io2.value) << 2) |
                (int(self.bus.io1.value) << 1) |
                int(self.bus.io0.value)
            )
            byte = (byte << 4) | nibble  # Combine the nibble into the byte
        return byte

```
qspi_slave.py
```python
import cocotb
from cocotb.triggers import RisingEdge, FallingEdge
from cocotb.handle import SimHandle

class QspiSlave:
    def __init__(self, bus: QspiBus, memory_size: int = 256):
        # Initialize QSPI bus and memory
        self.bus = bus
        self.memory = [0xFF] * memory_size  # Initialize memory with all bytes set to 0xFF

    async def run(self):
        # Main loop to handle transactions
        while True:
            await FallingEdge(self.bus.cs)
            while not self.bus.cs.value:
                await self._handle_transaction()

    async def _handle_transaction(self):
        # Handle incoming transactions based on commands
        command = await self._read_byte()
        if command == 0x02:  # Write command
            address = await self._read_address()
            data = await self._read_byte()
            self.memory[address] = data
        elif command == 0x03:  # Read command
            address = await self._read_address()
            await self._write_byte(self.memory[address])
        elif command == 0x20:  # Erase command
            address = await self._read_address()
            self.memory[address] = 0xFF

    async def _write_byte(self, byte):
        for i in range(2):  # Two cycles for 8 bits, as each cycle writes 4 bits
            nibble = (byte >> (4 * (1 - i))) & 0xF  # Extract 4 bits (nibble)
            self.bus.io0.value = (nibble >> 0) & 1  # Set the value for io0
            self.bus.io1.value = (nibble >> 1) & 1  # Set the value for io1
            self.bus.io2.value = (nibble >> 2) & 1  # Set the value for io2
            self.bus.io3.value = (nibble >> 3) & 1  # Set the value for io3
            await RisingEdge(self.bus.sclk)
        await Timer(1, units='ns')

    async def _read_byte(self):
        byte = 0
        for i in range(2):  # Two cycles for 8 bits, as each cycle reads 4 bits
            await RisingEdge(self.bus.sclk)
            # Read 4 bits from the QSPI lines and combine them into a nibble
            nibble = (
                (int(self.bus.io3.value) << 3) |
                (int(self.bus.io2.value) << 2) |
                (int(self.bus.io1.value) << 1) |
                int(self.bus.io0.value)
            )
            byte = (byte << 4) | nibble  # Combine the nibble into the byte
        return byte

```
### QSPI Flash Memory Interface Documentation

#### Overview
This document provides a detailed explanation of the QSPI Flash Memory Interface, implemented in Verilog, and its verification using Cocotb. The interface allows for read, write, and erase operations on the QSPI flash memory using four data lines (IO0, IO1, IO2, IO3).

### Interface Description
The QSPI (Quad Serial Peripheral Interface) is designed for communication between a master (e.g., a microcontroller) and a slave (e.g., flash memory). The interface includes the following signals:

| Signal Name   | Direction | Description                                      |
|---------------|-----------|--------------------------------------------------|
| `qspi_sclk`   | Input     | QSPI serial clock input                          |
| `qspi_cs`     | Input     | QSPI chip select input                           |
| `qspi_io0`    | Inout     | QSPI data line 0 (MOSI in single SPI mode)       |
| `qspi_io1`    | Inout     | QSPI data line 1 (MISO in single SPI mode)       |
| `qspi_io2`    | Inout     | QSPI data line 2                                 |
| `qspi_io3`    | Inout     | QSPI data line 3                                 |
| `reset_n`     | Input     | Active-low reset input                           |
| `clk`         | Input     | Clock input for internal logic                   |
| `write_enable`| Input     | Write enable signal                              |
| `read_enable` | Input     | Read enable signal                               |
| `erase_enable`| Input     | Erase enable signal                              |
| `data_in`     | Input     | Data input for write operation                   |
| `address`     | Input     | Address input for memory access                  |
| `data_out`    | Output    | Data output for read operation                   |

### Verilog Module
The Verilog module `qspi_flash` is responsible for handling the memory operations based on the given signals. Below is the Verilog code for the QSPI Flash Memory module:

```verilog
module qspi_flash (
    input wire qspi_sclk,        // QSPI serial clock input
    input wire qspi_cs,          // QSPI chip select input
    inout wire qspi_io0,         // QSPI data line 0 (MOSI in single SPI mode)
    inout wire qspi_io1,         // QSPI data line 1 (MISO in single SPI mode)
    inout wire qspi_io2,         // QSPI data line 2
    inout wire qspi_io3,         // QSPI data line 3
    input wire reset_n,          // Active-low reset input
    input wire clk,              // Clock input for internal logic
    input wire write_enable,     // Write enable signal
    input wire read_enable,      // Read enable signal
    input wire erase_enable,     // Erase enable signal
    input wire [7:0] data_in,    // Data input for write operation
    input wire [7:0] address,    // Address input for memory access
    output reg [7:0] data_out    // Data output for read operation
);

reg [7:0] memory [0:255];       // Memory array to store data, 256 bytes in size
reg [7:0] data_buffer;          // Buffer to handle bidirectional data lines

always @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
        data_out <= 8'hFF;      // Initialize data_out to 0xFF on reset
    end else begin
        if (write_enable) begin
            memory[address] <= data_in;    // Write data_in to memory at specified address
        end
        if (read_enable) begin
            data_out <= memory[address];   // Read data from memory at specified address
        end
        if (erase_enable) begin
            memory[address] <= 8'hFF;      // Erase data by writing 0xFF to memory at specified address
        end
    end
end

// Assign QSPI data lines based on operation mode
assign qspi_io0 = (write_enable || erase_enable) ? data_in[0] : 1'bz;
assign qspi_io1 = (write_enable || erase_enable) ? data_in[1] : 1'bz;
assign qspi_io2 = (write_enable || erase_enable) ? data_in[2] : 1'bz;
assign qspi_io3 = (write_enable || erase_enable) ? data_in[3] : 1'bz;

endmodule
```

### Cocotb Testbench
The following Python code provides a Cocotb testbench for verifying the QSPI Flash Memory module. The testbench includes methods for initializing the device, writing to memory, reading from memory, and erasing memory.

#### QSPIFlash Class
The `QSPIFlash` class encapsulates the functionality needed to interact with the QSPI flash memory.

```python
import cocotb
from cocotb.triggers import Timer
from cocotb.clock import Clock
from cocotbext.qspi import QspiBus, QspiMaster, QspiSlave, QspiConfig

class QSPIFlash:
    def __init__(self, dut):
        # Initialize QSPIFlash class with the DUT (Device Under Test)
        self.dut = dut
        
        # Initialize QSPI bus using the prefix 'qspi' from the DUT signals
        self.qspi_bus = QspiBus.from_prefix(dut, "qspi")
        
        # Configure QSPI communication parameters
        self.qspi_config = QspiConfig(
            word_width=8,
            sclk_freq=25e6,  # SCLK frequency of 25 MHz
            cpol=False,      # Clock polarity (CPOL) = 0
            cpha=False,      # Clock phase (CPHA) = 0
            msb_first=True,  # Most significant bit first
            cs_active_low=True  # Chip select is active low
        )
        
        # Initialize QSPI master with the configured bus and settings
        self.qspi_master = QspiMaster(self.qspi_bus, self.qspi_config)

    async def reset(self):
        # Reset the device by toggling the reset_n signal
        self.dut.reset_n.value = 0
        await Timer(100, units='ns')  # Wait for 100 ns
        self.dut.reset_n.value = 1
        await Timer(100, units='ns')  # Wait for another 100 ns

    async def initialize(self):
        # Start the clock with a period of 10 ns
        cocotb.start_soon(Clock(self.dut.clk, 10, units='ns').start())
        
        # Call the reset method to initialize the device
        await self.reset()

    async def write(self, address, data):
        # Send a write command along with address and data
        command = [0x02]  # Write command
        address_bytes = [(address >> i) & 0xFF for i in (16, 8, 0)]  # Split address into bytes
        data_bytes = [data]  # Convert data to bytes
        await self.qspi_master.write(command + address_bytes + data_bytes)  # Send command, address, and data
        await self.qspi_master.wait()  # Wait for QSPI transaction to complete

    async def read(self, address):
        # Send a read command along with address to read data
        command = [0x03]  # Read command
        address_bytes = [(address >> i) & 0xFF for i in (16, 8, 0)]  # Split address into bytes
        await self.qspi_master.write(command + address_bytes)  # Send command and address
        await self.qspi_master.wait()  # Wait for QSPI transaction to complete
        
        # Read one byte of data from QSPI
        read_data = await self.qspi_master.read(1)
        
        # Handle high-impedance state by resolving to 0xFF
        read_data_resolved = int(read_data[0].value) if read_data[0].value.is_resolvable else 0xFF
        
        return read_data_resolved

    async def erase(self, address):
        # Send a sector erase command along with address
        command = [0x20]  # Sector erase command
        address_bytes = [(address >> i) & 0xFF for i in (16, 8, 0)]  # Split address into bytes
        await self.qspi_master.write(command + address_bytes)  # Send command and address
        await self.qspi_master.wait()  # Wait for QSPI transaction to complete

```

#### Test Cases
Two test cases are provided to verify the write/read and erase functionalities of the QSPI flash memory.

##### Test Case: Write and Read
```python
@cocotb.test()
async def test_qspi_flash_write_read(dut):
    flash = QSPIFlash(dut)
    await flash.initialize()
    
    address = 0x00
    data_to_write = 0xA5
    await flash.write(address, data_to_write)
    await Timer(10, units='ns')
    
    read_data = await flash.read(address)
    assert read_data == data_to_write, f"Data mismatch: {read_data} != {data_to_write}"
```

##### Test Case: Erase
```python
@cocotb.test()
async def test_qspi_flash_erase(dut):
    flash = QSPIFlash(dut)
    await flash.initialize()
    
    address = 0x00
    data_to_write = 0x5A
    await flash.write(address, data_to_write)
    await Timer(10, units='ns')
    
    await flash.erase(address)
    await Timer(10, units='ns')
    
    read_data = await flash.read(address)
    assert read_data == 0xFF, f"Data after erase mismatch: {read_data} != 0xFF"
```

### QSPI Flash Test Module
The Verilog test module `qspi_flash_test` sets up the testbench environment to simulate the QSPI flash memory interface.

```verilog
module qspi_flash_test;
    reg qspi_sclk;             // QSPI serial clock
    reg qspi_mosi;             // QSPI master output, slave input
    wire qspi_miso;            // QSPI master input, slave output
    reg qspi_cs;               // QSPI chip select
    reg reset_n;               // Active-low reset signal
    reg clk;                   // Clock signal
    reg write_enable;          // Write enable signal
    reg read_enable;           // Read enable signal
    reg erase_enable;          // Erase enable signal
    reg [7:0] data_in

;         // Data input for memory operations
    reg [7:0] address;         // Address input for memory operations
    wire [7:0] data_out;       // Data output from memory operations

    qspi_flash dut (
        .qspi_sclk(qspi_sclk),
        .qspi_cs(qspi_cs),
        .qspi_io0(qspi_io0),
        .qspi_io1(qspi_io1),
        .qspi_io2(qspi_io2),
        .qspi_io3(qspi_io3),
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
        
        qspi_sclk = 0;
        qspi_io0 = 0,
        qspi_io1 = 0,
        qspi_io2 = 0,
        qspi_io3 = 0,
        qspi_cs = 1;
        reset_n = 0;
        clk = 0;
        write_enable = 0;
        read_enable = 0;
        erase_enable = 0;
        data_in = 0;
        address = 0;
        
        #10 reset_n = 1;
    end

    always #5 clk = ~clk;
endmodule
```

### Conclusion
This documentation provides a comprehensive guide to implementing and simulating a QSPI flash memory interface using Verilog and Cocotb. The QSPI interface supports essential memory operations such as read, write, and erase, and the provided testbench ensures these functionalities are correctly verified. Adjust and expand the simulation code as necessary to meet your specific requirements.
