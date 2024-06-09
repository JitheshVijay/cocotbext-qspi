import cocotb
from cocotb.triggers import Timer
from cocotbext.qspi.qspi_flash import QspiFlash

@cocotb.test()
async def test_qspi_flash_write_read(dut):
    print("Starting test_qspi_flash_write_read")
    qspi = QspiFlash(dut)
    await qspi.initialize()

    address = 0x01
    data_to_write = 0xA5
    await qspi.write(address, data_to_write)
    await Timer(10, units='ns')

    read_data = await qspi.read(address)
    print(f"Written data: {data_to_write}, Read data: {read_data}")
    assert read_data == data_to_write, f"Data mismatch: {read_data} != {data_to_write}"

@cocotb.test()
async def test_qspi_flash_erase(dut):
    print("Starting test_qspi_flash_erase")
    qspi = QspiFlash(dut)
    await qspi.initialize()

    address = 0x01
    data_to_write = 0x5A
    await qspi.write(address, data_to_write)
    await Timer(10, units='ns')

    await qspi.erase(address)
    await Timer(10, units='ns')

    read_data = await qspi.read(address)
    print(f"Data after erase: {read_data}")
    assert read_data == 0xFF, f"Data after erase mismatch: {read_data} != 0xFF"



