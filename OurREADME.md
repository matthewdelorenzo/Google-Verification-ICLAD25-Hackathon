# GenAI Hackathon Submission: SLM-Driven Design Verification

## Problem Category

**GenAI for Design Verification (Google)**

---

## Solution Architecture

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

