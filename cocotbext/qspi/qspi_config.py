"""Configuration for a QSPI transfer."""


class QspiConfig:
    def __init__(self, word_width=8, sclk_freq=1e6, cpol=False, cpha=False,
                 cs_active_low=True, io_mode="quad"):
        self.word_width = word_width
        self.sclk_freq = sclk_freq
        self.cpol = cpol
        self.cpha = cpha
        self.cs_active_low = cs_active_low
        self.io_mode = io_mode

    @property
    def lanes(self) -> int:
        """Data lines carrying bits simultaneously."""
        return {"single": 1, "dual": 2, "quad": 4}[self.io_mode]

    def __str__(self):
        return (f"QspiConfig(word_width={self.word_width}, "
                f"sclk_freq={self.sclk_freq}, cpol={self.cpol}, "
                f"cpha={self.cpha}, cs_active_low={self.cs_active_low}, "
                f"io_mode={self.io_mode})")
