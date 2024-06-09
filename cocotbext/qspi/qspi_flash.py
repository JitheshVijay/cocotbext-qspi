import cocotb
from cocotb.triggers import RisingEdge, ReadOnly
from cocotbext.qspi.qspi_bus import QspiBus

class QspiFlash:
    def __init__(self, dut):
        self.dut = dut
        self.qspi_bus = QspiBus.from_prefix(dut, "QSPI")

    async def initialize(self):
        self.qspi_bus.cs.value = 1
        await RisingEdge(self.qspi_bus.clk)

    async def write(self, address, data):
        self.qspi_bus.cs.value = 0
        await RisingEdge(self.qspi_bus.clk)
        self.dut.address.value = address
        self.dut.data_in.value = data
        self.dut.write_enable.value = 1
        await RisingEdge(self.qspi_bus.clk)
        self.dut.write_enable.value = 0
        self.qspi_bus.cs.value = 1

    async def read(self, address):
        self.qspi_bus.cs.value = 0
        await RisingEdge(self.qspi_bus.clk)
        self.dut.address.value = address
        self.dut.read_enable.value = 1
        await RisingEdge(self.qspi_bus.clk)
        await ReadOnly()
        data = self.dut.data_out.value.integer
        self.dut.read_enable.value = 0
        self.qspi_bus.cs.value = 1
        return data

    async def erase(self, address):
        self.qspi_bus.cs.value = 0
        await RisingEdge(self.qspi_bus.clk)
        self.dut.address.value = address
        self.dut.erase_enable.value = 1
        await RisingEdge(self.qspi_bus.clk)
        self.dut.erase_enable.value = 0
        self.qspi_bus.cs.value = 1
