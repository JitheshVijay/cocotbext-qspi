"""QSPI flash verification for cocotb."""

from pathlib import Path


def verilog_dir() -> Path:
    """Directory holding this package's Verilog models.

    The models ship inside the package, so a testbench can point at them
    without vendoring a copy:

        VERILOG_SOURCES += $(shell python -c \
            "import cocotbext.qspi as q; print(q.verilog_dir())")/qspi_flash.v
    """
    return Path(__file__).parent / "verilog"


from .qspi_bus import QspiBus
from .qspi_config import QspiConfig
from .qspi_flash import (
    QspiFlash,
    CMD_READ, CMD_QIOR2, CMD_QIOR4,
    CMD_WREN, CMD_WRDI, CMD_RDSR, CMD_RDID, CMD_PP, CMD_SE,
    STATUS_WIP, STATUS_WEL,
)
from .qspi_master import QspiMaster

__all__ = [
    "QspiBus", "QspiConfig", "QspiFlash", "QspiMaster",
    "CMD_READ", "CMD_QIOR2", "CMD_QIOR4",
    "CMD_WREN", "CMD_WRDI", "CMD_RDSR", "CMD_RDID", "CMD_PP", "CMD_SE",
    "STATUS_WIP", "STATUS_WEL",
]
