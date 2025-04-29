# Cython Implementation of CXXRTL Models

This document explains the Cython implementation of the simulation models in the ChipFlow examples project.

## Overview

The simulation infrastructure has been enhanced to support two alternative methods:
1. **Standard C++ Models**: The original implementation using pure C++ models
2. **Cython Models**: A new implementation that uses Cython to wrap the C++ models, providing a more Python-friendly interface

Additionally, the Cython implementation includes support for the CXXRTL CAPI, which provides a more comprehensive interface to the CXXRTL simulation core.

## Structure

The Cython implementation consists of several components:

1. **Core CXXRTL CAPI Bindings**: Located in `my_design/sim/cython_models/cxxrtl_capi.pyx` and `my_design/sim/cython_models/cxxrtl_capi_wrap.h`
2. **Model Implementations**: Located in `my_design/sim/cython_models/models.pyx`
3. **Python Interface Module**: Located in `my_design/sim/cython_models/cxxrtl_capi_module.py`
4. **Build Scripts**: `setup.py` for the models and `setup_capi.py` for the CXXRTL CAPI bindings

## How It Works

### CXXRTL CAPI Bindings

The CXXRTL CAPI bindings provide a Python interface to the core CXXRTL simulation API. This includes:

- `Design` class for accessing the top-level design
- `Object` class for accessing signals and modules
- `VcdWriter` class for generating VCD waveform files

The bindings are implemented in Cython, which compiles to C++ code that interfaces with the CXXRTL C API.

### Model Implementations

The simulation models (SPI Flash, UART, GPIO, etc.) are implemented in Cython, which allows for efficient execution while maintaining a Python-like syntax. The models interact with the CXXRTL simulation through thin wrapper classes (`PyValue1`, `PyValue4`, etc.) that provide access to the underlying CXXRTL values.

### Integration with the Simulation

The simulation is controlled by the `MySimStep` class in `my_design/steps/sim.py`, which:

1. Checks configuration options to determine which simulation mode to use
2. Builds the appropriate simulation components
3. Runs the simulation

## Running the Simulation

The simulation mode can be controlled through the configuration in `chipflow.toml`:

```toml
[sim]
use_cython = true          # Set to false for C++ models
use_cxxrtl_capi = true     # Set to true to use CXXRTL CAPI
```

To run the simulation:

```bash
pdm run chipflow sim
```

## Performance Considerations

The Cython implementation offers several potential advantages:

1. **Improved Development Experience**: More Python-like syntax for model implementation
2. **Enhanced Debugging**: Better integration with Python debugging tools
3. **Performance**: While there is some overhead from the Python/C++ boundary, the critical parts of the simulation are still executed in compiled C++

The CXXRTL CAPI provides additional capabilities, such as:

1. **Better Signal Access**: More comprehensive access to signals and hierarchical objects
2. **Standard API**: A consistent API for interacting with the simulation

## Technical Details

### PyValue Classes

The `PyValue1`, `PyValue4`, and `PyValue8` classes provide a Python interface to the CXXRTL value template. These classes wrap the C++ `cxxrtl::value<N>` template and provide methods to get and set values, as well as access individual bits.

### JSON and Event Handling

The simulation uses JSON for configuration and event logging. The Cython implementation maintains compatibility with the C++ implementation, using the same event log format and command handling mechanism.

### Simulator Integration

The simulation runs through a C++ entry point (`cython_main.cc`) that creates the simulation objects and connects them to Python through the Cython bindings. This approach maintains compatibility with the existing CXXRTL simulation infrastructure while adding the flexibility of Python.