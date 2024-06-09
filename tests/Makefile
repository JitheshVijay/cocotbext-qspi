# Makefile for running Cocotb tests with Icarus Verilog

# Language and simulator settings
TOPLEVEL_LANG ?= verilog
SIM ?= icarus
WAVES ?= 1

# Time unit and precision
COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps

# Name of the top-level module and the test module
DUT      = qspi_flash
TOPLEVEL = $(DUT)
MODULE   = test_qspi_flash

# Verilog source files
VERILOG_SOURCES = $(shell pwd)/verilog/qspi_flash.v $(shell pwd)/verilog/qspi_flash_test.v

# Enable waveform dumping
ifeq ($(SIM), icarus)
	PLUSARGS += -fst

	ifeq ($(WAVES), 1)
		VERILOG_SOURCES += iverilog_dump.v
		COMPILE_ARGS += -s iverilog_dump
	endif
endif

# Include the cocotb makefile
include $(shell cocotb-config --makefiles)/Makefile.sim

# Generate the iverilog dump file for waveform output
iverilog_dump.v:
	echo 'module iverilog_dump();' > $@
	echo 'initial begin' >> $@
	echo '    $$dumpfile("$(TOPLEVEL).fst");' >> $@
	echo '    $$dumpvars(0, $(TOPLEVEL));' >> $@
	echo 'end' >> $@
	echo 'endmodule' >> $@

# Clean target to remove generated files
clean::
	@rm -rf iverilog_dump.v
	@rm -rf dump.fst $(TOPLEVEL).fst
	@rm -rf results.xml
	@rm -rf sim_build

.PHONY: all sim clean

