# Jack-binary-Compiler 🛠️

This repository contains a multi-stage compiler built from scratch, translating code from a high-level, object-oriented language down to binary machine code. 

The project is structured into three main assignments, directly inspired by the *Nand2Tetris* (Building a Modern Computer from First Principles) curriculum. The entire toolchain is implemented in **Python**.

## 📂 Project Structure

- **`Assign1/`**: Assembler (Assembly to Binary)
- **`Assign2/`**: VM Translator (VM Bytecode to Assembly)
- **`Assign3/`**: Jack Compiler (Jack High-Level Language to VM Bytecode)

---

##  The Pipeline (Assignments)

### Assignment 1: The Assembler (`assembly to binary`)
The first stage in the lower-level execution pipeline. This module translates programs written in Hack Assembly language (`.asm` files) into binary machine code (`.hack` files) that can be directly executed by the computer's hardware.
* **Input**: `filename.asm`
* **Output**: `filename.hack`
* **Features**: Handles white space, instructions (A-instructions and C-instructions), and symbol resolution (variables and loop labels).

### Assignment 2: The VM Translator (`vm to assembly`)
The intermediate stage. This module translates programs written in stack-based Virtual Machine bytecode (`.vm` files) into Hack Assembly language (`.asm` files).
* **Input**: `filename.vm` or a directory of `.vm` files.
* **Output**: `filename.asm`
* **Features**: Implements arithmetic and logical commands, memory access commands (push/pop), program flow commands (branching), and function calling commands.

### Assignment 3: The Jack Compiler (`jack to vm`)
The highest-level stage. This module compiles the Java-like, object-oriented "Jack" programming language (`.jack` files) into Virtual Machine bytecode (`.vm` files).
* **Input**: `filename.jack` or a directory of `.jack` files.
* **Output**: `filename.vm`
* **Features**: Consists of a **Tokenizer** (lexical analysis) and an **Engine** (syntax analysis and code generation), handling expressions, statements, classes, and subroutines.

---


