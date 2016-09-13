################################################################
#
# Makefile for bfr P4 project
#
################################################################

export TARGET_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

include ../../init.mk

ifndef P4FACTORY
P4FACTORY := $(TARGET_ROOT)/../..
endif
MAKEFILES_DIR := ${P4FACTORY}/makefiles

# This target's P4 name
export P4_INPUT := p4src/bfr.p4
export P4_NAME := bfr

# Common defines targets for P4 programs
include ${MAKEFILES_DIR}/common.mk

# Put custom targets in bfr-local.mk
-include bfr-local.mk

all:bm

