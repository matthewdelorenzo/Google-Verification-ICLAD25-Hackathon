#!/usr/bin/env python3

import re
import argparse
import random
from pathlib import Path

def parse_verilog_module(file_path):
    """Parse a Verilog file to extract module name, inputs, and outputs."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract module name
    module_match = re.search(r'module\s+(\w+)', content)
    if not module_match:
        raise ValueError(f"Couldn't find module definition in {file_path}")
    module_name = module_match.group(1)
    
    # Extract ports
    # Look for module ... (port_list);
    module_decl = re.search(r'module\s+\w+\s*\((.*?)\);', content, re.DOTALL)
    if not module_decl:
        raise ValueError(f"Couldn't parse module ports in {file_path}")
    
    port_list = module_decl.group(1)
    
    # Extract input and output declarations
    inputs = []
    outputs = []
    
    # Find input declarations like: input [7:0] data;
    input_matches = re.finditer(r'input\s+(?:wire|reg)?\s*(?:\[(\d+):(\d+)\])?\s*(\w+)', content)
    for match in input_matches:
        msb, lsb, name = match.groups()
        width = int(msb) - int(lsb) + 1 if msb and lsb else 1
        inputs.append((name, width))
    
    # Find output declarations
    output_matches = re.finditer(r'output\s+(?:wire|reg)?\s*(?:\[(\d+):(\d+)\])?\s*(\w+)', content)
    for match in output_matches:
        msb, lsb, name = match.groups()
        width = int(msb) - int(lsb) + 1 if msb and lsb else 1
        outputs.append((name, width))
    
    return module_name, inputs, outputs

def generate_testbench(golden_file, buggy_file, output_file):
    """Generate a testbench to find differences between the two modules."""
    golden_module, golden_inputs, golden_outputs = parse_verilog_module(golden_file)
    buggy_module, buggy_inputs, buggy_outputs = parse_verilog_module(buggy_file)
    
    # Verify that both modules have the same interface
    if sorted(golden_inputs) != sorted(buggy_inputs):
        raise ValueError("Input ports don't match between the two modules")
    if sorted(golden_outputs) != sorted(buggy_outputs):
        raise ValueError("Output ports don't match between the two modules")
    
    inputs = golden_inputs
    outputs = golden_outputs
    
    with open(output_file, 'w') as f:
        # Write testbench header
        f.write(f"`timescale 1ns/1ps\n\n")
        f.write(f"module testbench;\n\n")
        
        # Declare registers and wires
        for name, width in inputs:
            if width == 1:
                f.write(f"  reg {name};\n")
            else:
                f.write(f"  reg [{width-1}:0] {name};\n")
        
        f.write("\n")
        
        for name, width in outputs:
            if width == 1:
                f.write(f"  wire {name}_golden, {name}_buggy;\n")
            else:
                f.write(f"  wire [{width-1}:0] {name}_golden, {name}_buggy;\n")
        
        f.write("\n")
        
        # Instantiate both modules
        f.write(f"  // Golden reference module\n")
        f.write(f"  {golden_module} golden_inst (\n")
        port_connections = []
        for name, _ in inputs:
            port_connections.append(f"    .{name}({name})")
        for name, _ in outputs:
            port_connections.append(f"    .{name}({name}_golden)")
        f.write(",\n".join(port_connections))
        f.write("\n  );\n\n")
        
        f.write(f"  // Buggy module\n")
        f.write(f"  {buggy_module} buggy_inst (\n")
        port_connections = []
        for name, _ in inputs:
            port_connections.append(f"    .{name}({name})")
        for name, _ in outputs:
            port_connections.append(f"    .{name}({name}_buggy)")
        f.write(",\n".join(port_connections))
        f.write("\n  );\n\n")
        
        # Define clock if needed (assuming there might be a clock)
        if any(name == "clk" or name == "clock" for name, _ in inputs):
            f.write("  // Clock generation\n")
            f.write("  initial begin\n")
            f.write("    clk = 0;\n")
            f.write("    forever #5 clk = ~clk;\n")
            f.write("  end\n\n")
        
        # Main testbench logic
        f.write("  // Test variables\n")
        f.write("  integer errors = 0;\n")
        f.write("  integer num_tests = 1000;\n\n")
        
        f.write("  initial begin\n")
        f.write("    $display(\"Starting equivalence checking...\");\n")
        f.write("    $display(\"Testing random inputs to find discrepancies\");\n\n")
        
        # Reset logic if needed
        if any(name == "rst" or name == "reset" for name, _ in inputs):
            f.write("    // Reset sequence\n")
            f.write("    rst = 1;\n")
            f.write("    #20;\n")
            f.write("    rst = 0;\n")
            f.write("    #10;\n\n")
        
        # Random testing
        f.write("    // Random testing\n")
        f.write("    for (int i = 0; i < num_tests; i++) begin\n")
        f.write("      // Generate random inputs\n")
        for name, width in inputs:
            if name not in ["clk", "clock", "rst", "reset"]:
                f.write(f"      {name} = $urandom")
                if width > 32:
                    # For wide signals, might need multiple random values
                    f.write(f" & {(1 << width) - 1}")
                f.write(";\n")
        
        f.write("\n      #10; // Wait for outputs to stabilize\n\n")
        
        # Compare outputs
        f.write("      // Compare outputs\n")
        for name, width in outputs:
            f.write(f"      if ({name}_golden !== {name}_buggy) begin\n")
            f.write(f"        $display(\"Mismatch found for output {name} at time %t!\", $time);\n")
            f.write(f"        $display(\"  Inputs:\");\n")
            for in_name, _ in inputs:
                if in_name not in ["clk", "clock"]:
                    f.write(f"        $display(\"    {in_name} = %h\", {in_name});\n")
            f.write(f"        $display(\"  Golden output: {name} = %h\", {name}_golden);\n")
            f.write(f"        $display(\"  Buggy output:  {name} = %h\", {name}_buggy);\n")
            f.write(f"        errors = errors + 1;\n")
            f.write(f"        // Stop at first mismatch - comment out to find more\n")
            f.write(f"        $finish;\n")
            f.write(f"      end\n")
        
        f.write("    end\n\n")
        
        f.write("    if (errors == 0) begin\n")
        f.write("      $display(\"No discrepancies found after %0d tests.\", num_tests);\n")
        f.write("      $display(\"Modules may be equivalent or need more thorough testing.\");\n")
        f.write("    end else begin\n")
        f.write("      $display(\"%0d discrepancies found.\", errors);\n")
        f.write("    end\n")
        f.write("    $finish;\n")
        f.write("  end\n\n")
        
        f.write("endmodule\n")
    
    print(f"Testbench generated: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a Verilog equivalence checking testbench")
    parser.add_argument("golden_file", help="Path to the golden reference Verilog file")
    parser.add_argument("buggy_file", help="Path to the buggy Verilog file")
    parser.add_argument("-o", "--output", default="testbench.sv", help="Output testbench file")
    
    args = parser.parse_args()
    generate_testbench(args.golden_file, args.buggy_file, args.output)