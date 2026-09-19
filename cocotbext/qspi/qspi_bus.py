"""Signal bundle for a quad-SPI bus."""


class QspiBus:
    """The wires a QSPI master drives, grouped together.

    ``io_out``/``io_oe`` are the master's half of the bidirectional data bus:
    a simulator will not let a testbench drive an ``inout`` net directly, so
    the top level splits it into a value and a **per-lane** output enable.
    Per-lane is not a detail -- in single-lane mode the master drives io0
    while the device answers on io1, so a single bus-wide enable would make
    the two collide.
    """

    def __init__(self, clk, cs, io, io_out, io_oe):
        self.clk = clk
        self.cs = cs
        self.io = io
        self.io_out = io_out
        self.io_oe = io_oe

    @classmethod
    def from_entity(cls, entity, clk="clk", cs="csb", io="io"):
        """Pick the bus signals out of ``entity`` by name."""
        return cls(
            clk=getattr(entity, clk),
            cs=getattr(entity, cs),
            io=getattr(entity, io),
            io_out=entity.io_out,
            io_oe=entity.io_oe,
        )
