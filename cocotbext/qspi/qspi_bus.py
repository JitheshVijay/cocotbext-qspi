"""Signal bundle for a quad-SPI bus."""

from cocotb.handle import HierarchyObject


class QspiBus:
    """The wires a QSPI master drives, grouped together.

    ``io_out``/``io_oe`` are the master's half of the bidirectional data bus:
    a simulator cannot have the testbench drive an ``inout`` net directly, so
    the top level splits it into a value and an output enable. Dropping
    ``io_oe`` releases the bus so the slave can drive read data onto it.
    """

    def __init__(self, clk, cs, io, io_out, io_oe):
        self.clk = clk        # QSPI_CLK
        self.cs = cs          # QSPI_CS, active low
        self.io = io          # QSPI_IO, read back for slave-driven data
        self.io_out = io_out  # master's driven value
        self.io_oe = io_oe    # master's output enable

    @classmethod
    def from_entity(cls, entity: HierarchyObject, prefix: str = "QSPI"):
        """Pick the bus signals out of ``entity`` by name."""
        return cls(
            clk=getattr(entity, f"{prefix}_CLK"),
            cs=getattr(entity, f"{prefix}_CS"),
            io=getattr(entity, f"{prefix}_IO"),
            io_out=entity.io_out,
            io_oe=entity.io_oe,
        )

    # Kept for callers written against the previous name.
    from_prefix = from_entity
