import cocotb
from cocotb.triggers import Timer
from qspi_flash_api import QSPIFlash  # Import the QSPIFlash class from qspi_flash_api module

# Test to write data to and read data from QSPI flash memory
@cocotb.test()
async def test_qspi_flash_write_read(dut):
    flash = QSPIFlash(dut)  # Initialize QSPIFlash object with the DUT
    
    await flash.initialize()  # Initialize the QSPI flash device
    
    # Write data to QSPI flash memory
    address = 0x00  # Address to write data to
    data_to_write = 0xA5  # Data to be written
    await flash.write(address, data_to_write)  # Call write method to write data
    await Timer(10, units='ns')  # Wait for 10 ns
    
    # Read data from QSPI flash memory
    read_data = await flash.read(address)  # Call read method to read data
    
    # Verify the read data matches the data that was written
    assert read_data == data_to_write, f"Data mismatch: {read_data} != {data_to_write}"

# Test to erase data from QSPI flash memory
@cocotb.test()
async def test_qspi_flash_erase(dut):
    flash = QSPIFlash(dut)  # Initialize QSPIFlash object with the DUT
    
    await flash.initialize()  # Initialize the QSPI flash device
    
    # Write data to QSPI flash memory
    address = 0x00  # Address to write data to
    data_to_write = 0x5A  # Data to be written
    await flash.write(address, data_to_write)  # Call write method to write data
    await Timer(10, units='ns')  # Wait for 10 ns
    
    # Erase data from QSPI flash memory
    await flash.erase(address)  # Call erase method to erase data
    await Timer(10, units='ns')  # Wait for 10 ns
    
    # Read data from QSPI flash memory after erase
    read_data = await flash.read(address)  # Call read method to read data
    
    # After erase, the default state of the memory should be 0xFF
    assert read_data == 0xFF, f"Data after erase mismatch: {read_data} != 0xFF"

