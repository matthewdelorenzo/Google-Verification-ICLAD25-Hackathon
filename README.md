# GenAI Hackathon Submission: SLM-Driven Design Verification

## Problem Category

**GenAI for Design Verification (Google)**

---

## Solution Architecture

To generate the testbenches that correctly identify the golden Verilog code out of the 31 options, we take a unique approach.
As opposed to directly generating the testbench, we instead leverage the text processing capabilities of the LLM by generating our own RTL code from the natural langauge specification.
Assuming this Verilog is correct, we then create a unique testbench for each Verilog instance by creating an automated equivalence checking script.
This creates a set of testbenches that we can simulate, and if our code is correct, only one tesbench will pass for the given verilog problem.
We can then use this as our final Verilog testbench.

Our approach consists of two main components:

### 1. SPEC Generation Using SLM Models

- **Input:** Natural language description of the design.
- **Process:** An SLM parses the description and generates a formal SPEC RTL.
- **Output:** A machine-readable SPEC to serve as the "golden design".

### 2. Automated Equivalence Checking (RTL2RTL Checking)

- **Inputs:**  
  - Generated SPEC (golden reference)  
  - RTL implementation under test
- **Process:**  
  - All possible stimulus/input sequences are applied.
  - Outputs from both the SPEC and the RTL implementation are compared cycle by cycle.
- **Decision:**  
  - The implementation **passes** if all outputs match for all stimulus.  
  - Any mismatch indicates a **bug** in the implementation.

---

## Advantages

1. **Robustness:**  
   - Variability in LLM/SLM outputs does **not** adversely impact testbench accuracy. As long as the generated golden SPEC is correct, buggy implementations are reliably detected.
2. **Portability:**  
   - The framework is easily extendable to different designs with minimal changes (just update the natural language spec).
3. **Scalability:**  
   - The approach scales effortlessly for larger or more complex designs.

---

## Results

We were able to create a full pipeline that can generate these testbenches (see agent.py).
Due to some techincal difficulties with AnythingLLM, we currently do not have the testbenches submitted to the repository.
However, for each problem repostiory, we did upload our golden Verilog code (generated with our local model QWEN-2.5B-Instruct), which can be utilized with our framework to generate the associated testbenches.
