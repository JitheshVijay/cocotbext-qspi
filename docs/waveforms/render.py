#!/usr/bin/env python3
"""Turn capture.vcd into WaveDrom diagrams for the README.

Everything drawn here comes out of a real simulation -- capture.py runs the
transactions, Icarus dumps the VCD, and this samples it. Nothing is drawn by
hand, so the diagrams cannot drift away from what the model actually does.

    make        # produces capture.vcd
    make svg    # runs this
"""

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
VCD = HERE / "capture.vcd"


# ── VCD parsing ──────────────────────────────────────────────────────

def parse_vcd(path):
    """Return (id -> name, list of (time, id, value)) from a VCD file."""
    names, changes = {}, []
    scope = []
    time = 0
    var_re = re.compile(r"\$var\s+\w+\s+\d+\s+(\S+)\s+(\S+)(?:\s+\[[^\]]*\])?\s+\$end")

    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if line.startswith("$scope"):
                scope.append(line.split()[2])
            elif line.startswith("$upscope"):
                scope.pop()
            elif line.startswith("$var"):
                match = var_re.match(line)
                if match:
                    ident, name = match.groups()
                    # Only the top level; the DUT mirrors the same wires.
                    if len(scope) == 1:
                        names[ident] = name
            elif line.startswith("#"):
                time = int(line[1:])
            elif line and line[0] in "01xzXZ" and len(line) > 1:
                changes.append((time, line[1:], line[0]))
            elif line.startswith(("b", "B")):
                value, ident = line[1:].split(None, 1)
                changes.append((time, ident.strip(), value))
    return names, changes


class Signals:
    """Value of every signal over time, queryable at an instant."""

    def __init__(self, names, changes):
        self.by_name = {}
        ident_to_name = names
        for time, ident, value in changes:
            name = ident_to_name.get(ident)
            if name is None:
                continue
            self.by_name.setdefault(name, []).append((time, value))
        for series in self.by_name.values():
            series.sort(key=lambda item: item[0])

    def at(self, name, time):
        """Last value of ``name`` at or before ``time``."""
        result = "x"
        for stamp, value in self.by_name.get(name, []):
            if stamp > time:
                break
            result = value
        return result

    def edges(self, name, value="1"):
        """Times at which ``name`` takes ``value``."""
        return [t for t, v in self.by_name.get(name, []) if v == value]


def as_int(value):
    """VCD bit string to int, or None when it contains x/z."""
    bits = value.strip()
    if not bits or any(c not in "01" for c in bits):
        return None
    return int(bits, 2)


# ── transaction slicing ──────────────────────────────────────────────

def transactions(sig):
    """Chip-select-low windows, as (start, end) times."""
    series = sig.by_name.get("csb", [])
    windows, start = [], None
    for time, value in series:
        if value == "0" and start is None:
            start = time
        elif value == "1" and start is not None:
            windows.append((start, time))
            start = None
    return windows


def clocks_in(sig, start, end):
    """Rising clock edges strictly inside a window."""
    return [t for t in sig.edges("clk", "1") if start < t < end]


def opcode_of(sig, start, end):
    """Decode the single-lane opcode a transaction begins with."""
    bits = ""
    for edge in clocks_in(sig, start, end)[:8]:
        value = sig.at("io", edge)
        bits += value[-1] if value and value[-1] in "01" else "x"
    return int(bits, 2) if len(bits) == 8 and "x" not in bits else None


# ── WaveDrom emission ────────────────────────────────────────────────

def pad_vcd(raw, width):
    """Extend a VCD vector value to ``width`` bits.

    VCD strips leading zeros on vectors, and extends with the leading value
    when it is x or z, so "0" on a 4-bit bus means "0000" and "z" means
    "zzzz". Slicing the raw string without this returns short values and the
    cells come out blank.
    """
    if not raw:
        return ""
    fill = raw[0] if raw[0] in "xzXZ" else "0"
    return raw.rjust(width, fill)


def cell_value(sig, edge, width=4):
    """What the io bus carries this clock, and who is driving it.

    Returns (label, driver) where driver is "M" (master), "D" (device) or
    None (nobody -- a dummy or turnaround cycle).
    """
    oe = as_int(sig.at("io_oe", edge))
    raw = sig.at("io", edge)

    padded = pad_vcd(raw, width)

    if oe:
        lanes = bin(oe).count("1")
        # Only the driven lanes carry meaning: in single-lane mode io1..io3
        # float, so reading the whole bus would give x.
        bits = padded[-lanes:]
        if bits and all(c in "01" for c in bits):
            value = int(bits, 2)
            return (str(value) if lanes == 1 else f"{value:X}"), "M"
        return "", "M"

    # Master released: work out how wide the device's answer is by seeing
    # which lanes it actually drives. Checked widest first, because a quad
    # read drives io0 too and would otherwise look like a dual one.
    def driven(lanes):
        bits = padded[-lanes:]
        return bits if len(bits) == lanes and all(c in "01" for c in bits) else None

    quad = driven(4)
    if quad:
        return f"{int(quad, 2):X}", "D"

    dual = driven(2)
    if dual:
        return f"{int(dual, 2):X}", "D"

    # Single-lane reads answer on io1 (MISO) while io0 floats.
    if len(padded) >= 2 and padded[-2] in "01":
        return padded[-2], "D"
    return "", None


def build_wave(sig, start, end, title, max_clocks=64):
    """WaveJSON for one transaction, one cell per clock."""
    edges = clocks_in(sig, start, end)[:max_clocks]

    # WaveDrom repeats a character to mean "redraw the transition"; "." holds
    # the level. csb goes low once and stays there for the whole window.
    csb_wave = "10" + "." * (len(edges) - 1)

    io_wave, io_data = [], []
    drv_wave, drv_data = [], []

    for edge in edges:
        label, driver = cell_value(sig, edge)

        if driver == "M":
            io_wave.append("4")          # master drives
        elif driver == "D":
            io_wave.append("5")          # device drives
        else:
            io_wave.append("x")          # nobody: dummy / turnaround
        if driver is not None:
            io_data.append(label)

        if driver is None:
            drv_wave.append("x")
        else:
            drv_wave.append("=" if driver == "M" else "6")
            drv_data.append(driver)

    return {
        "signal": [
            {"name": "clk", "wave": "p" + "." * (len(edges) - 1)},
            {"name": "csb", "wave": csb_wave[:len(edges) + 1]},
            {"name": "io", "wave": "".join(io_wave), "data": io_data},
            {"name": "driver", "wave": "".join(drv_wave), "data": drv_data},
        ],
        "head": {"text": title},
        "config": {"hscale": 1},
    }


def annotate(wave, spans, clocks):
    """Add a phase ruler under the diagram."""
    total = sum(count for _, count in spans)
    if total > clocks:
        spans = spans[:]
        while spans and total > clocks:
            name, count = spans[-1]
            trim = min(count, total - clocks)
            spans[-1] = (name, count - trim)
            total -= trim
            if spans[-1][1] == 0:
                spans.pop()
    ruler = "".join("=" + "." * (count - 1) for _, count in spans if count)
    tail = clocks - sum(c for _, c in spans if c)
    if tail > 0:
        ruler += "=" + "." * (tail - 1)
    wave["signal"].append({})
    wave["signal"].append({
        "name": "",
        "wave": ruler,
        "data": [name for name, count in spans if count] + ([""] if tail > 0 else []),
    })
    return wave


def render(wave, out_path):
    source = out_path.with_suffix(".json")
    source.write_text(json.dumps(wave, indent=2))
    subprocess.run(
        ["npx", "--yes", "wavedrom-cli", "-i", str(source), "-s", str(out_path)],
        check=True, cwd=HERE,
    )
    source.unlink()
    return out_path


def comparison(sig, found, path):
    """One row per read width, so the clock cost is visible side by side."""
    rows = []
    for opcode, label in ((0x03, "single"),
                          (0xBB, "dual"),
                          (0xEB, "quad")):
        if opcode not in found:
            continue
        start, end = found[opcode]
        edges = clocks_in(sig, start, end)
        wave, data = [], []
        for edge in edges:
            cell, driver = cell_value(sig, edge)
            if driver == "M":
                wave.append("4")
            elif driver == "D":
                wave.append("5")
            else:
                wave.append("x")
            if driver is not None:
                data.append(cell)
        rows.append({"name": f"{label} {len(edges)}clk",
                     "wave": "".join(wave), "data": data})

    wave = {
        "signal": rows,
        "head": {"text": "One byte, three widths: 40 / 36 / 26 clocks "
                         "(master orange, device blue, nobody hatched)"},
        "config": {"hscale": 1},
    }
    return render(wave, path)


def main():
    if not VCD.exists():
        sys.exit("capture.vcd missing -- run `make` first")

    names, changes = parse_vcd(VCD)
    sig = Signals(names, changes)
    windows = transactions(sig)

    found = {}
    for start, end in windows:
        opcode = opcode_of(sig, start, end)
        found.setdefault(opcode, (start, end))

    wanted = {
        0xEB: ("quad-read.svg",
               "Fast read quad I/O (0xEB): single-lane opcode, then four lanes",
               [("opcode 0xEB (1 lane)", 8), ("address (4 lanes)", 6),
                ("mode (4)", 2), ("dummy", 8), ("data (4 lanes)", 2)]),
        0x05: ("read-status.svg",
               "Read status (0x05): WIP is set while the program is in flight",
               [("opcode 0x05", 8), ("status byte", 8)]),
    }

    written = []
    for opcode, (filename, title, spans) in wanted.items():
        if opcode not in found:
            print(f"  no 0x{opcode:02X} transaction in the capture; skipped")
            continue
        start, end = found[opcode]
        clocks = len(clocks_in(sig, start, end))
        wave = build_wave(sig, start, end, title)
        annotate(wave, spans, min(clocks, 64))
        written.append(render(wave, HERE / filename).name)
        print(f"  {written[-1]}")

    written.append(comparison(sig, found, HERE / "width-comparison.svg").name)
    print(f"  {written[-1]}")

    print(f"\n{len(written)} diagram(s) written")


if __name__ == "__main__":
    main()
