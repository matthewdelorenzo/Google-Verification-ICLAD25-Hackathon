"""Agent definition that generates a testbench."""

import constants

# -------- Helper Functions
import re
import argparse
import random
from pathlib import Path
import subprocess
import tempfile
import subprocess
import os

def simulate_verilog(golden_str, buggy_str, testbench_str):
    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        golden_path = os.path.join(tmpdir, "golden.v")
        buggy_path = os.path.join(tmpdir, "buggy.v")
        testbench_path = os.path.join(tmpdir, "testbench.v")
        output_path = os.path.join(tmpdir, "tb.out")

        # Write Verilog strings to files
        with open(golden_path, 'w') as f:
            f.write(golden_str)
        with open(buggy_path, 'w') as f:
            f.write(buggy_str)
        with open(testbench_path, 'w') as f:
            f.write(testbench_str)

        # Compile using iverilog
        subprocess.run(["iverilog", "-o", output_path, testbench_path, golden_path, buggy_path], check=True)

        # Run simulation with vvp
        result = subprocess.run(["vvp", output_path], capture_output=True, text=True)

        return result.stdout  # or result.stderr if needed


def parse_verilog_module_from_string(content):
    """Parse a Verilog string to extract module name, inputs, and outputs."""
    # Extract module name
    module_match = re.search(r'module\s+(\w+)', content)
    if not module_match:
        raise ValueError("Couldn't find module definition.")
    module_name = module_match.group(1)

    # Extract ports
    module_decl = re.search(r'module\s+\w+\s*\((.*?)\);', content, re.DOTALL)
    if not module_decl:
        raise ValueError("Couldn't parse module ports.")
    port_list = module_decl.group(1)

    # Extract input and output declarations as dictionaries
    inputs = {}
    outputs = {}

    input_matches = re.finditer(r'input\s+(?:wire|reg)?\s*(?:\[(\d+):(\d+)\])?\s*(\w+)', content)
    for match in input_matches:
        msb, lsb, name = match.groups()
        width = int(msb) - int(lsb) + 1 if msb and lsb else 1
        inputs[name] = width

    output_matches = re.finditer(r'output\s+(?:wire|reg)?\s*(?:\[(\d+):(\d+)\])?\s*(\w+)', content)
    for match in output_matches:
        msb, lsb, name = match.groups()
        width = int(msb) - int(lsb) + 1 if msb and lsb else 1
        outputs[name] = width

    return module_name, inputs, outputs

def generate_testbench_from_strings(golden_source, buggy_source):
    """Generate a Verilog testbench as a string to compare two modules."""
    golden_module, golden_inputs, golden_outputs = parse_verilog_module_from_string(golden_source)
    buggy_module, buggy_inputs, buggy_outputs = parse_verilog_module_from_string(buggy_source)

    # Verify that both modules have the same interface by name
    if set(golden_inputs.keys()) != set(buggy_inputs.keys()):
        missing_in_golden = set(buggy_inputs.keys()) - set(golden_inputs.keys())
        missing_in_buggy = set(golden_inputs.keys()) - set(buggy_inputs.keys())
        
        error_msg = "Input ports don't match between the two modules\n"
        if missing_in_golden:
            error_msg += f"Inputs in buggy but not in golden: {missing_in_golden}\n"
        if missing_in_buggy:
            error_msg += f"Inputs in golden but not in buggy: {missing_in_buggy}\n"
        raise ValueError(error_msg)
    
    if set(golden_outputs.keys()) != set(buggy_outputs.keys()):
        missing_in_golden = set(buggy_outputs.keys()) - set(golden_outputs.keys())
        missing_in_buggy = set(golden_outputs.keys()) - set(buggy_outputs.keys())
        
        error_msg = "Output ports don't match between the two modules\n"
        if missing_in_golden:
            error_msg += f"Outputs in buggy but not in golden: {missing_in_golden}\n"
        if missing_in_buggy:
            error_msg += f"Outputs in golden but not in buggy: {missing_in_buggy}\n"
        raise ValueError(error_msg)
    
    # Check for width mismatches
    for port_name, golden_width in golden_inputs.items():
        buggy_width = buggy_inputs[port_name]
        if golden_width != buggy_width:
            raise ValueError(f"Width mismatch for input port '{port_name}': golden={golden_width}, buggy={buggy_width}")
    
    for port_name, golden_width in golden_outputs.items():
        buggy_width = buggy_outputs[port_name]
        if golden_width != buggy_width:
            raise ValueError(f"Width mismatch for output port '{port_name}': golden={golden_width}, buggy={buggy_width}")

    lines = []
    lines.append("`timescale 1ns/1ps\n")
    lines.append("module testbench;\n")

    # Declare inputs
    for name, width in golden_inputs.items():
        if width == 1:
            lines.append(f"  reg {name};")
        else:
            lines.append(f"  reg [{width-1}:0] {name};")
    lines.append("")

    # Declare outputs
    for name, width in golden_outputs.items():
        if width == 1:
            lines.append(f"  wire {name}_golden, {name}_buggy;")
        else:
            lines.append(f"  wire [{width-1}:0] {name}_golden, {name}_buggy;")
    lines.append("")

    # Instantiate modules
    def generate_instance(inst_name, module_name, ports_dict, suffix):
        lines.append(f"  // {inst_name} module")
        lines.append(f"  {module_name} {inst_name}_inst (")
        port_connections = []
        for name in ports_dict['inputs'].keys():
            port_connections.append(f"    .{name}({name})")
        for name in ports_dict['outputs'].keys():
            port_connections.append(f"    .{name}({name}_{suffix})")
        lines.append(",\n".join(port_connections))
        lines.append("  );\n")

    generate_instance("golden", golden_module, {'inputs': golden_inputs, 'outputs': golden_outputs}, "golden")
    generate_instance("buggy", buggy_module, {'inputs': buggy_inputs, 'outputs': buggy_outputs}, "buggy")

    # Optional clock generation
    clock_name = None
    if "clk" in golden_inputs:
        clock_name = "clk"
    elif "clock" in golden_inputs:
        clock_name = "clock"
    
    if clock_name:
        lines.append("  // Clock generation")
        lines.append("  initial begin")
        lines.append(f"    {clock_name} = 0;")
        lines.append(f"    forever #5 {clock_name} = ~{clock_name};")
        lines.append("  end\n")

    # Begin test logic
    lines.append("  integer errors = 0;")
    lines.append("  integer num_tests = 1000;\n")
    lines.append("  initial begin")
    lines.append("    $display(\"Starting equivalence checking...\");")
    lines.append("    $display(\"Testing random inputs to find discrepancies\");\n")

    # Reset logic if needed
    reset_name = None
    if "rst" in golden_inputs:
        reset_name = "rst"
    elif "reset" in golden_inputs:
        reset_name = "reset"
    
    if reset_name:
        lines.append(f"    // Reset sequence")
        lines.append(f"    {reset_name} = 1;")
        lines.append(f"    #20;")
        lines.append(f"    {reset_name} = 0;")
        lines.append(f"    #10;\n")

    # Random input loop
    lines.append("    for (int i = 0; i < num_tests; i++) begin")
    lines.append("      // Generate random inputs")
    for name, width in golden_inputs.items():
        if name not in ["clk", "clock", "rst", "reset"]:
            if width > 32:
                lines.append(f"      {name} = $urandom & {(1 << width) - 1};")
            else:
                lines.append(f"      {name} = $urandom;")
    lines.append("\n      #10; // Wait for outputs to stabilize\n")

    # Compare outputs
    lines.append("      // Compare outputs")
    for name, width in golden_outputs.items():
        lines.append(f"      if ({name}_golden !== {name}_buggy) begin")
        lines.append(f"        $display(\"Mismatch found for output {name} at time %t!\", $time);")
        lines.append("        $display(\"  Inputs:\");")
        for in_name in golden_inputs.keys():
            if in_name not in ["clk", "clock"]:
                lines.append(f"        $display(\"    {in_name} = %h\", {in_name});")
        lines.append(f"        $display(\"  Golden output: {name} = %h\", {name}_golden);")
        lines.append(f"        $display(\"  Buggy output:  {name} = %h\", {name}_buggy);")
        lines.append("        errors = errors + 1;")
        lines.append("        $finish;")
        lines.append("      end")
    lines.append("    end\n")

    lines.append("    if (errors == 0) begin")
    lines.append("      $display(\"No discrepancies found after %0d tests.\", num_tests);")
    lines.append("      $display(\"Modules may be equivalent or need more thorough testing.\");")
    lines.append("    end else begin")
    lines.append("      $display(\"%0d discrepancies found.\", errors);")
    lines.append("    end")
    lines.append("    $finish;")
    lines.append("  end\n")
    lines.append("endmodule")

    return "\n".join(lines)

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Generate a Verilog equivalence checking testbench")
#     parser.add_argument("golden_file", help="Path to the golden reference Verilog file")
#     parser.add_argument("buggy_file", help="Path to the buggy Verilog file")
#     parser.add_argument("-o", "--output", default="testbench.sv", help="Output testbench file")
    
#     args = parser.parse_args()
#     generate_testbench(args.golden_file, args.buggy_file, args.output)


# TODO: Implement this.
def generate_testbench(file_name_to_content: dict[str, str]) -> str:
    spec = file_name_to_content['specification.md']
    file_name_to_content.pop('tb.v')
    # send spec file to llm in prompt using the api

    golden_file = spec # this will be the result of the llm prompt
    generated_tbs_dict = {}
    
    for filename in file_name_to_content.keys:
        if filename[-1] == 'v':
            generated_tbs_dict[filename] = generate_testbench_from_strings(golden_file, file_name_to_content[filename])


    tb_pass_fail = {}
    for inst in generated_tbs_dict.key:
        tb_pass_fail[inst] = simulate_verilog(golden_file, file_name_to_content[inst], generated_tbs_dict[inst])

    print(tb_pass_fail)

    del file_name_to_content
    return constants.DUMMY_TESTBENCH




