"""
CXXRTL CAPI Python Module

This module provides a higher-level Python interface to the Cython CXXRTL CAPI bindings.
It simplifies common operations and provides helper functions for working with CXXRTL.
"""

import os
import sys
from pathlib import Path

# Try to import the Cython bindings
try:
    from . import cxxrtl_capi
except ImportError:
    # Provide a helpful error message
    raise ImportError(
        "CXXRTL CAPI bindings not found. "
        "Please build them first with: "
        "cd my_design/sim/cython_models && python setup_capi.py build_ext --inplace"
    )

# Re-export the main classes
Design = cxxrtl_capi.Design
Object = cxxrtl_capi.Object
VcdWriter = cxxrtl_capi.VcdWriter

# Helper functions
def create_design_from_file(design_file, top_path=None):
    """
    Create a Design instance from a shared library file containing the CXXRTL design.
    
    Args:
        design_file: Path to the shared library (.so/.dll) file
        top_path: Optional path to use as the top level in the design hierarchy
        
    Returns:
        A Design instance if successful, None otherwise
    """
    import ctypes
    
    # Ensure the file exists
    if not os.path.exists(design_file):
        print(f"Design file not found: {design_file}")
        return None
        
    try:
        # Load the shared library
        lib = ctypes.cdll.LoadLibrary(design_file)
        
        # Find the design create function (conventionally named <design>_create)
        create_funcs = [name for name in dir(lib) if name.endswith('_create')]
        if not create_funcs:
            print(f"No design create function found in {design_file}")
            return None
            
        # Use the first create function found
        create_func = getattr(lib, create_funcs[0])
        create_func.restype = ctypes.c_void_p
        
        # Create the design toplevel
        toplevel = create_func()
        if not toplevel:
            print(f"Failed to create design toplevel from {design_file}")
            return None
            
        # Create the design
        if top_path:
            return Design.from_toplevel(toplevel, top_path)
        else:
            return Design.from_toplevel(toplevel)
            
    except Exception as e:
        print(f"Error creating design from {design_file}: {e}")
        return None

def run_simulation(design, clock_name, reset_name=None, num_cycles=100, vcd_file=None):
    """
    Run a simulation for the specified number of cycles.
    
    Args:
        design: A Design instance
        clock_name: Name of the clock signal
        reset_name: Optional name of the reset signal
        num_cycles: Number of cycles to simulate
        vcd_file: Optional filename to write VCD waveform data
        
    Returns:
        True if simulation completed successfully, False otherwise
    """
    if not design:
        print("No design provided")
        return False
        
    # Get the clock signal
    clock = design.get_object(clock_name)
    if not clock:
        print(f"Clock signal not found: {clock_name}")
        return False
        
    # Get the reset signal if specified
    reset = None
    if reset_name:
        reset = design.get_object(reset_name)
        if not reset:
            print(f"Reset signal not found: {reset_name}")
            
    # Create VCD writer if needed
    vcd = None
    if vcd_file:
        vcd = VcdWriter()
        vcd.set_timescale(1, "ns")
        vcd.add_all_from_design_without_memories(design)
        
    # Run simulation
    print(f"Running simulation for {num_cycles} cycles...")
    design.reset()
    
    for cycle in range(num_cycles):
        # Apply reset if needed (active for first few cycles)
        if reset and cycle < 5:
            reset.set_value(1)
        elif reset:
            reset.set_value(0)
            
        # Toggle clock (posedge)
        clock.set_value(1)
        design.eval()
        design.commit()
        
        # Sample VCD if enabled
        if vcd:
            vcd.sample(cycle * 2)
            
        # Toggle clock (negedge)
        clock.set_value(0)
        design.eval()
        design.commit()
        
        # Sample VCD if enabled
        if vcd:
            vcd.sample(cycle * 2 + 1)
            
        # Print progress every 10 cycles
        if cycle % 10 == 0:
            print(f"Completed {cycle} cycles")
            
    # Write VCD file if enabled
    if vcd and vcd_file:
        print(f"Writing VCD data to {vcd_file}")
        vcd.write_to_file(vcd_file)
        
    print(f"Simulation completed: {num_cycles} cycles")
    return True