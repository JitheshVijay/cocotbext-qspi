# Runs one short simulation and dumps a VCD for render.py to draw from.
#
#   make        # capture.vcd
#   make svg    # capture.vcd -> *.svg  (needs npx wavedrom-cli)

TOPLEVEL_LANG ?= verilog
SIM ?= icarus

COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps

SIM_BUILD = sim_build_waves

TOPLEVEL = qspi_flash_test
MODULE   = capture

VERILOG_SOURCES  = $(shell pwd)/../../verilog/qspi_flash.v
VERILOG_SOURCES += $(shell pwd)/../../verilog/qspi_flash_test.v
VERILOG_SOURCES += vcd_dump.v
COMPILE_ARGS += -s vcd_dump

export PYTHONPATH := $(shell pwd)/../..:$(shell pwd):$(PYTHONPATH)
export COCOTB_HDL_TIMEUNIT
export COCOTB_HDL_TIMEPRECISION

include $(shell cocotb-config --makefiles)/Makefile.sim

# Plain VCD rather than the suites' FST: render.py parses it directly, and
# the file is small enough that the extra size does not matter.
sim results.xml: vcd_dump.v
vcd_dump.v:
	echo 'module vcd_dump();' > $@
	echo 'initial begin' >> $@
	echo '    $$dumpfile("capture.vcd");' >> $@
	echo '    $$dumpvars(0, $(TOPLEVEL));' >> $@
	echo 'end' >> $@
	echo 'endmodule' >> $@

svg: results.xml
	python3 render.py

clean::
	@rm -rf $(SIM_BUILD) results.xml vcd_dump.v capture.vcd
