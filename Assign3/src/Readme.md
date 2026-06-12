# DA2304 Assignment 3 — Jack Compiler Pipeline

## Overview

This is a full compiler frontend for the **Jack programming language** .  
It takes `.jack` source files and produces three output artefacts per file:

```
Conv.jack  →  ConvT.xml   (tokeniser output — flat token list)
           →  Conv.xml    (parse-tree XML   — grammatical structure)
           →  Conv.vm     (VM code          — ready for VM Translator)
```

---

## File Structure

```
src/
├── JackCompiler.py        ← pipeline entry point (run this)
├── JackTokenizer.py       ← lexical analyser (Stage 1)
├── CompilationEngine.py   ← recursive-descent parser + VM code generator (Stage 2 & 3)
├── SymbolTable.py         ← two-scope symbol table (class + subroutine)
├── VMWriter.py            ← writes .vm instructions to file
└── README.md              ← this file

jack/
├── Conv.jack              ← 2D convolution class
└── Main.jack              ← driver program (5×5 test)

out/
├── ConvT.xml              ← tokeniser output for Conv.jack
├── Conv.xml               ← parse tree for Conv.jack
├── Conv.vm                ← VM code for Conv.jack
├── MainT.xml
├── Main.xml
└── Main.vm
```

---

## Requirements

- **Python 3.7 or higher**
- No external libraries needed — standard library only

Check your Python version:
```bash
python --version
```

---

## How to Run

All five source files (`JackCompiler.py`, `JackTokenizer.py`, `CompilationEngine.py`,
`SymbolTable.py`, `VMWriter.py`) must be in the **same directory** when running.

### Compile a single `.jack` file

```bash
python JackCompiler.py Conv.jack
```

Output files are written **next to the input file**:
```
Conv.jack  →  ConvT.xml, Conv.xml, Conv.vm
```

### Compile an entire directory

```bash
python JackCompiler.py path/to/jack/
```

Every `.jack` file in the directory is compiled. Example:
```bash
python JackCompiler.py ../jack/
```
This will compile both `Conv.jack` and `Main.jack` and write all six output files.

### Expected terminal output

```
Compiling directory: jack/
  Compiling: jack/Conv.jack
    → jack/ConvT.xml
    → jack/Conv.xml
    → jack/Conv.vm
  Compiling: jack/Main.jack
    → jack/MainT.xml
    → jack/Main.xml
    → jack/Main.vm
Done.
```
