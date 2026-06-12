"""
JackCompiler.py
"""

import sys
import os
from JackTokenizer     import JackTokenizer
from CompilationEngine import CompilationEngine


def compile_file(jack_path: str) -> None:
    """Compile a single .jack file and write the three output artefacts."""
    base       = os.path.splitext(jack_path)[0]   # strip .jack
    token_xml  = base + "T.xml"
    parse_xml  = base + ".xml"
    vm_file    = base + ".vm"

    print(f"  Compiling: {jack_path}")

    # ── Stage 1: Tokenise ──────────────────────────────────────────────
    tokenizer = JackTokenizer(jack_path)
    tokens    = tokenizer.tokenize()          # returns list, also sets internal state
    tokenizer.export_xml(token_xml)
    print(f"    → {token_xml}")

    # ── Stage 2 + 3: Parse & generate VM ──────────────────────────────
    engine = CompilationEngine(tokens, parse_xml, vm_file)
    engine.compile_class()                    # writes parse_xml and vm_file, then closes
    print(f"    → {parse_xml}")
    print(f"    → {vm_file}")


def compile_directory(dir_path: str) -> None:
    """Compile all .jack files found in dir_path."""
    jack_files = [
        os.path.join(dir_path, f)
        for f in os.listdir(dir_path)
        if f.endswith(".jack")
    ]
    if not jack_files:
        print(f"No .jack files found in '{dir_path}'.")
        return
    for jf in sorted(jack_files):
        compile_file(jf)


def main():
    if len(sys.argv) != 2:
        print("Usage: python JackCompiler.py <file.jack | directory>")
        sys.exit(1)

    source = sys.argv[1]

    if os.path.isdir(source):
        print(f"Compiling directory: {source}")
        compile_directory(source)
    elif os.path.isfile(source) and source.endswith(".jack"):
        print(f"Compiling file: {source}")
        compile_file(source)
    else:
        print(f"Error: '{source}' is not a .jack file or a directory.")
        sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
