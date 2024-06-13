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
        sclk = getattr(entity, f"{prefix}_CLK")
        cs = getattr(entity, f"{prefix}_cs")
        io0 = getattr(entity, f"{prefix}_io0")
        io1 = getattr(entity, f"{prefix}_io1")
        io2 = getattr(entity, f"{prefix}_io2")
        io3 = getattr(entity, f"{prefix}_io3")
        return cls(sclk, cs, io0, io1, io2, io3)
