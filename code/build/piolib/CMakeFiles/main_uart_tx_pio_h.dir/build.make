# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 3.17

# Delete rule output on recipe failure.
.DELETE_ON_ERROR:


#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:


# Disable VCS-based implicit rules.
% : %,v


# Disable VCS-based implicit rules.
% : RCS/%


# Disable VCS-based implicit rules.
% : RCS/%,v


# Disable VCS-based implicit rules.
% : SCCS/s.%


# Disable VCS-based implicit rules.
% : s.%


.SUFFIXES: .hpux_make_needs_suffix_list


# Command-line flag to silence nested $(MAKE).
$(VERBOSE)MAKESILENT = -s

# Suppress display of executed commands.
$(VERBOSE).SILENT:


# A target that is always out of date.
cmake_force:

.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /opt/local/bin/cmake

# The command to remove a file.
RM = /opt/local/bin/cmake -E rm -f

# Escaping for special characters.
EQUALS = =

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /Users/masonwright/Documents/card_sat/code

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /Users/masonwright/Documents/card_sat/code/build

# Utility rule file for main_uart_tx_pio_h.

# Include the progress variables for this target.
include piolib/CMakeFiles/main_uart_tx_pio_h.dir/progress.make

piolib/CMakeFiles/main_uart_tx_pio_h: piolib/uart_tx.pio.h


piolib/uart_tx.pio.h: ../piolib/uart_tx.pio
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --blue --bold --progress-dir=/Users/masonwright/Documents/card_sat/code/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Generating uart_tx.pio.h"
	cd /Users/masonwright/Documents/card_sat/code/build/piolib && ../pioasm/pioasm -o c-sdk /Users/masonwright/Documents/card_sat/code/piolib/uart_tx.pio /Users/masonwright/Documents/card_sat/code/build/piolib/uart_tx.pio.h

main_uart_tx_pio_h: piolib/CMakeFiles/main_uart_tx_pio_h
main_uart_tx_pio_h: piolib/uart_tx.pio.h
main_uart_tx_pio_h: piolib/CMakeFiles/main_uart_tx_pio_h.dir/build.make

.PHONY : main_uart_tx_pio_h

# Rule to build all files generated by this target.
piolib/CMakeFiles/main_uart_tx_pio_h.dir/build: main_uart_tx_pio_h

.PHONY : piolib/CMakeFiles/main_uart_tx_pio_h.dir/build

piolib/CMakeFiles/main_uart_tx_pio_h.dir/clean:
	cd /Users/masonwright/Documents/card_sat/code/build/piolib && $(CMAKE_COMMAND) -P CMakeFiles/main_uart_tx_pio_h.dir/cmake_clean.cmake
.PHONY : piolib/CMakeFiles/main_uart_tx_pio_h.dir/clean

piolib/CMakeFiles/main_uart_tx_pio_h.dir/depend:
	cd /Users/masonwright/Documents/card_sat/code/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /Users/masonwright/Documents/card_sat/code /Users/masonwright/Documents/card_sat/code/piolib /Users/masonwright/Documents/card_sat/code/build /Users/masonwright/Documents/card_sat/code/build/piolib /Users/masonwright/Documents/card_sat/code/build/piolib/CMakeFiles/main_uart_tx_pio_h.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : piolib/CMakeFiles/main_uart_tx_pio_h.dir/depend

