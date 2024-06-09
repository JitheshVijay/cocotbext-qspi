import cocotb
from cocotb.triggers import Timer, RisingEdge

class QspiSlave:
    def __init__(self, dut, config):
        self.dut = dut
        self.config = config

    async def read(self):
        byte = 0
        for i in range(2):  # 2 iterations, 4 bits each time
            await RisingEdge(self.dut.QSPI_CLK)
            for j in range(4):
                byte = (byte << 1) | int(self.dut.QSPI_IO[j].value)
        return byte

    async def write(self, data):
        for i in range(2):  # 2 iterations, 4 bits each time
            for j in range(4):
                self.dut.QSPI_IO[j].value = (data >> (7 - 4*i - j)) & 1
            await RisingEdge(self.dut.QSPI_CLK)
        await Timer(1, units='ns')
