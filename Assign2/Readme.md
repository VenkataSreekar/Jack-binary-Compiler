# DA2304 Assignment 2: Hack VM Translator & Matrix MAC Operations
 

## Overview
This repository contains a two-part solution for Assignment 2:
1. **The VM Translator:** A Python-based compiler that translates stack-based Hack Virtual Machine (`.vm`) commands into native Hack Assembly Language (`.asm`).
2. **Matrix MAC Operations:** A suite of modular `.vm` programs that perform Multiply-Accumulate (MAC) operations on matrices, specifically calculating `Y = (W * X) + B`, complete with dimension sanity checking.

## Project Structure
* `src/main.py` - The entry point script that handles file/directory parsing and translation logic.
* `src/HackVM.py` - The core module containing the `Parser` and `CodeWriter` classes.
* `MATMUL/` - Directory containing the modular matrix operation files:
  * `FullMAC.vm` - The combined orchestrator function that manages sanity checks, multiplication, and bias addition.
  * `MatMulOnly.vm` - Computes the core `Y = W * X` multiplication.
  * `AddBias.vm` - Computes the `Y = Y + B` addition via a flat 1D loop.
* `RowXCol.vm` - Subroutine to compute the dot product of a single row and column.

## Prerequisites
* **Python 3.x** must be installed on your system. No external libraries are required.

---

## How to Run the Translator and Create `.asm` Files

The translator can be executed from the command line in two distinct modes depending on whether you are translating a standalone function or a complete multi-file program. 

Open your terminal, navigate to the `src/` directory, and use the following commands:

### Mode 1: Translating a Single File
Use this mode if you want to translate an isolated `.vm` file. 
* **Note:** Single-file translation *does not* inject the `Sys.init` bootstrap code. It is meant for simple test scripts that manually initialize the RAM.

Run the following commands to convert the individual files inside the `MATMUL` folder:

```bash
# Translate the Dimension Validator
python main.py ../MATMUL/SanityCheck.vm

# Translate the core Matrix Multiplication function
python main.py ../MATMUL/MatMul.vm

# Translate the Bias Addition function
python main.py ../MATMUL/AddBias.vm

# Translate the Combined Orchestrator function
python main.py ../MATMUL/FullMAC.vm

# Translate the Row-by-Column Dot Product subroutine
python main.py ../MATMUL/RowXCol.vm