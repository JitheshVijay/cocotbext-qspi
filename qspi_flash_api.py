import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotbext.spi import SpiBus, SpiMaster, SpiConfig

class QSPIFlash:
    def __init__(self, dut):
        # Initialize QSPIFlash class with the DUT (Device Under Test)
        self.dut = dut
        
        # Initialize SPI bus using the prefix 'qspi' from the DUT signals
        self.spi_bus = SpiBus.from_prefix(dut, "qspi")
        
        # Configure SPI communication parameters
        self.spi_config = SpiConfig(
            word_width=8,
            sclk_freq=25e6,  # SCLK frequency of 25 MHz
            cpol=False,      # Clock polarity (CPOL) = 0
            cpha=False,      # Clock phase (CPHA) = 0
            msb_first=True,  # Most significant bit first
            cs_active_low=True  # Chip select is active low
        )
        
        # Initialize SPI master with the configured bus and settings
        self.spi_master = SpiMaster(self.spi_bus, self.spi_config)

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
        await self.spi_master.write(command + address_bytes + data_bytes)  # Send command, address, and data
        await self.spi_master.wait()  # Wait for SPI transaction to complete

    async def read(self, address):
        # Send a read command along with address to read data
        command = [0x03]  # Read command
        address_bytes = [(address >> i) & 0xFF for i in (16, 8, 0)]  # Split address into bytes
        await self.spi_master.write(command + address_bytes)  # Send command and address
        await self.spi_master.wait()  # Wait for SPI transaction to complete
        
        # Read one byte of data from SPI
        read_data = await self.spi_master.read(1)
        
        # Handle high-impedance state by resolving to 0xFF
        read_data_resolved = int(read_data[0].value) if read_data[0].value.is_resolvable else 0xFF
        
        return read_data_resolved

    async def erase(self, address):
        # Send a sector erase command along with address
        command = [0x20]  # Sector erase command
        address_bytes = [(address >> i) & 0xFF for i in (16, 8, 0)]  # Split address into bytes
        await self.spi_master.write(command + address_bytes)  # Send command and address
        await self.spi_master.wait()  # Wait for SPI transaction to complete

