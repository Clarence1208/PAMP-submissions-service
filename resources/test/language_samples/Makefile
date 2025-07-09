# Sample Makefile demonstrating various Make features

# Variables
PROJECT_NAME = sample_project
CC = gcc
CXX = g++
CFLAGS = -Wall -Wextra -std=c99 -O2
CXXFLAGS = -Wall -Wextra -std=c++17 -O2
LDFLAGS = -lm
SRCDIR = src
BUILDDIR = build
OBJDIR = $(BUILDDIR)/obj
BINDIR = $(BUILDDIR)/bin
TESTDIR = tests

# Source files
C_SOURCES = $(wildcard $(SRCDIR)/*.c)
CXX_SOURCES = $(wildcard $(SRCDIR)/*.cpp)
C_OBJECTS = $(C_SOURCES:$(SRCDIR)/%.c=$(OBJDIR)/%.o)
CXX_OBJECTS = $(CXX_SOURCES:$(SRCDIR)/%.cpp=$(OBJDIR)/%.o)
ALL_OBJECTS = $(C_OBJECTS) $(CXX_OBJECTS)

# Test files
TEST_SOURCES = $(wildcard $(TESTDIR)/*.c $(TESTDIR)/*.cpp)
TEST_OBJECTS = $(TEST_SOURCES:%.c=$(OBJDIR)/%.o)
TEST_OBJECTS := $(TEST_OBJECTS:%.cpp=$(OBJDIR)/%.o)

# Target executable
TARGET = $(BINDIR)/$(PROJECT_NAME)
TEST_TARGET = $(BINDIR)/test_$(PROJECT_NAME)

# Default target
.DEFAULT_GOAL := all

# Phony targets
.PHONY: all clean install uninstall test debug release help setup

# Main targets
all: setup release

release: CFLAGS += -DNDEBUG
release: CXXFLAGS += -DNDEBUG
release: $(TARGET)

debug: CFLAGS += -g -DDEBUG
debug: CXXFLAGS += -g -DDEBUG
debug: $(TARGET)

# Create directories
setup:
	@echo "Setting up build directories..."
	@mkdir -p $(OBJDIR) $(BINDIR)
	@mkdir -p $(OBJDIR)/$(TESTDIR)

# Link target executable
$(TARGET): $(ALL_OBJECTS) | $(BINDIR)
	@echo "Linking $@..."
	$(CXX) $(ALL_OBJECTS) -o $@ $(LDFLAGS)
	@echo "Build complete: $@"

# Test target
test: $(TEST_TARGET)
	@echo "Running tests..."
	@./$(TEST_TARGET)

$(TEST_TARGET): $(TEST_OBJECTS) $(filter-out $(OBJDIR)/main.o, $(ALL_OBJECTS)) | $(BINDIR)
	@echo "Linking test executable..."
	$(CXX) $^ -o $@ $(LDFLAGS)

# Compile C source files
$(OBJDIR)/%.o: $(SRCDIR)/%.c | $(OBJDIR)
	@echo "Compiling $<..."
	$(CC) $(CFLAGS) -c $< -o $@

# Compile C++ source files
$(OBJDIR)/%.o: $(SRCDIR)/%.cpp | $(OBJDIR)
	@echo "Compiling $<..."
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Compile test files
$(OBJDIR)/$(TESTDIR)/%.o: $(TESTDIR)/%.c | $(OBJDIR)/$(TESTDIR)
	@echo "Compiling test $<..."
	$(CC) $(CFLAGS) -I$(SRCDIR) -c $< -o $@

$(OBJDIR)/$(TESTDIR)/%.o: $(TESTDIR)/%.cpp | $(OBJDIR)/$(TESTDIR)
	@echo "Compiling test $<..."
	$(CXX) $(CXXFLAGS) -I$(SRCDIR) -c $< -o $@

# Create directories
$(OBJDIR):
	mkdir -p $(OBJDIR)

$(OBJDIR)/$(TESTDIR):
	mkdir -p $(OBJDIR)/$(TESTDIR)

$(BINDIR):
	mkdir -p $(BINDIR)

# Install target
install: $(TARGET)
	@echo "Installing $(PROJECT_NAME)..."
	@sudo cp $(TARGET) /usr/local/bin/
	@echo "Installation complete"

# Uninstall target
uninstall:
	@echo "Uninstalling $(PROJECT_NAME)..."
	@sudo rm -f /usr/local/bin/$(PROJECT_NAME)
	@echo "Uninstallation complete"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(BUILDDIR)
	@echo "Clean complete"

# Documentation generation
docs:
	@echo "Generating documentation..."
	@doxygen Doxyfile
	@echo "Documentation generated in docs/"

# Code formatting
format:
	@echo "Formatting code..."
	@find $(SRCDIR) -name "*.c" -o -name "*.cpp" -o -name "*.h" | xargs clang-format -i
	@echo "Code formatting complete"

# Static analysis
analyze:
	@echo "Running static analysis..."
	@cppcheck --enable=all --std=c99 --std=c++17 $(SRCDIR)/
	@echo "Static analysis complete"

# Memory check
memcheck: debug
	@echo "Running memory check..."
	@valgrind --leak-check=full --show-leak-kinds=all $(TARGET)

# Profiling
profile: debug
	@echo "Running profiler..."
	@gprof $(TARGET) gmon.out > profile.txt
	@echo "Profile saved to profile.txt"

# Package creation
package: release
	@echo "Creating package..."
	@tar -czf $(PROJECT_NAME)-$(shell date +%Y%m%d).tar.gz \
		$(TARGET) README.md LICENSE
	@echo "Package created: $(PROJECT_NAME)-$(shell date +%Y%m%d).tar.gz"

# Show file sizes
size: $(TARGET)
	@echo "Binary sizes:"
	@size $(TARGET)
	@ls -lh $(TARGET)

# Dependencies
depend:
	@echo "Generating dependencies..."
	@$(CC) -MM $(C_SOURCES) > .depend
	@$(CXX) -MM $(CXX_SOURCES) >> .depend

# Include dependencies if they exist
-include .depend

# Help target
help:
	@echo "Available targets:"
	@echo "  all       - Build the project (default)"
	@echo "  release   - Build optimized release version"
	@echo "  debug     - Build debug version with symbols"
	@echo "  test      - Build and run tests"
	@echo "  clean     - Remove build artifacts"
	@echo "  install   - Install to /usr/local/bin"
	@echo "  uninstall - Remove from /usr/local/bin"
	@echo "  docs      - Generate documentation"
	@echo "  format    - Format source code"
	@echo "  analyze   - Run static analysis"
	@echo "  memcheck  - Run memory check with valgrind"
	@echo "  profile   - Run profiler"
	@echo "  package   - Create distribution package"
	@echo "  size      - Show binary sizes"
	@echo "  depend    - Generate dependencies"
	@echo "  help      - Show this help message"

# Variable inspection (for debugging)
print-vars:
	@echo "PROJECT_NAME: $(PROJECT_NAME)"
	@echo "CC: $(CC)"
	@echo "CXX: $(CXX)"
	@echo "CFLAGS: $(CFLAGS)"
	@echo "CXXFLAGS: $(CXXFLAGS)"
	@echo "C_SOURCES: $(C_SOURCES)"
	@echo "CXX_SOURCES: $(CXX_SOURCES)"
	@echo "ALL_OBJECTS: $(ALL_OBJECTS)"
	@echo "TARGET: $(TARGET)" 