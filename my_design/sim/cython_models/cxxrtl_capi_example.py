"""
CXXRTL CAPI Cython Bindings Example

This example demonstrates how to use the CXXRTL CAPI Cython bindings
to control and interact with a CXXRTL simulation.
"""

import os
import sys
import time
from pathlib import Path

# Import the CXXRTL CAPI bindings
try:
    import cxxrtl_capi
except ImportError:
    print("CXXRTL CAPI bindings not found. Please build them first with:")
    print("  cd my_design/sim/cython_models && python setup_capi.py build_ext --inplace")
    sys.exit(1)

# External function to get the design toplevel (implementation-specific)
def get_design_toplevel():
    # This function needs to be implemented based on your specific design
    # It should return a cxxrtl_toplevel pointer
    # For example, it might call an exported function from a compiled module:
    #
    # from ctypes import cdll, c_void_p
    # lib = cdll.LoadLibrary("./sim_design.so")
    # get_toplevel_func = lib.design_create
    # get_toplevel_func.restype = c_void_p
    # return get_toplevel_func()
    #
    # For this example, we'll just return None to indicate this is a placeholder
    return None

def run_example_simulation():
    """
    Example simulation using the CXXRTL CAPI bindings.
    
    Note: This is a demonstration and won't run as-is since it needs
    an actual design toplevel to work with.
    """
    print("CXXRTL CAPI Example Simulation")
    
    # In a real scenario, you would get this from your compiled design
    toplevel = get_design_toplevel()
    if toplevel is None:
        print("No design toplevel available. This is just a demonstration.")
        print("To use this example with a real design, you need to implement")
        print("the get_design_toplevel() function to return a valid cxxrtl_toplevel.")
        return
    
    # Create a design from the toplevel
    design = cxxrtl_capi.Design.from_toplevel(toplevel)
    
    # Reset the design
    design.reset()
    
    # Get all objects in the design
    objects = design.get_all_objects()
    print(f"Found {len(objects)} objects in the design")
    
    # Print information about the first few objects
    for i, obj in enumerate(objects[:5]):
        print(f"Object {i}: {obj.name}, Type: {obj.type}, Width: {obj.width}, Flags: {obj.flags}")
    
    # Try to get a specific object (this is an example, adjust for your design)
    clk = design.get_object("\\top \\clk")
    reset = design.get_object("\\top \\reset")
    
    if clk and reset:
        # Create a VCD writer to record waveforms
        vcd = cxxrtl_capi.VcdWriter()
        vcd.set_timescale(1, "ns")
        vcd.add_all_from_design_without_memories(design)
        
        # Run simulation for 10 cycles
        print("Running simulation for 10 cycles...")
        for i in range(10):
            # Set clock and reset values
            if i < 2:  # Reset for first 2 cycles
                reset.set_value(1)
            else:
                reset.set_value(0)
                
            clk.set_value(i % 2)  # Toggle clock
            
            # Evaluate and commit the design
            design.eval()
            design.commit()
            
            # Sample VCD at current time
            vcd.sample(i)
            
            # Print simulation time
            print(f"Simulation time: {i}ns")
        
        # Write VCD to file
        vcd_file = "simulation.vcd"
        vcd.write_to_file(vcd_file)
        print(f"Wrote VCD to {vcd_file}")
    else:
        print("Couldn't find expected clock and reset signals")

if __name__ == "__main__":
    run_example_simulation()