# Makefile for running Cocotb tests with Icarus Verilog

# Language and simulator settings
# The models live inside the installed package, so tests use the same
# copy a user would get from pip rather than a repo-relative path.
VERILOG_DIR := $(shell PYTHONPATH=$(shell pwd)/.. python3 -c \
    "import cocotbext.qspi as q; print(q.verilog_dir())" 2>/dev/null)
ifeq ($(VERILOG_DIR),)
VERILOG_DIR := $(shell pwd)/../cocotbext/qspi/verilog
endif

TOPLEVEL_LANG ?= verilog
SIM ?= icarus
WAVES ?= 1

# Time unit and precision
COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps

# Name of the top-level module and the test module
DUT      = qspi_flash
TOPLEVEL = qspi_flash_test
MODULE   = test_qspi_flash

# Verilog source files
VERILOG_SOURCES = $(VERILOG_DIR)/qspi_flash.v
VERILOG_SOURCES += $(VERILOG_DIR)/qspi_flash_test.v

# Enable waveform dumping
ifeq ($(SIM), icarus)
	PLUSARGS += -fst

	ifeq ($(WAVES), 1)
		VERILOG_SOURCES += iverilog_dump.v
		COMPILE_ARGS += -s iverilog_dump
	endif
endif

# Make the repo root (for the cocotbext package) and this directory (for the
# test module) importable, so `make -C tests` works from a bare checkout
# without the caller having to set PYTHONPATH.
export PYTHONPATH := $(shell pwd)/..:$(shell pwd):$(PYTHONPATH)
export COCOTB_HDL_TIMEUNIT
export COCOTB_HDL_TIMEPRECISION

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
