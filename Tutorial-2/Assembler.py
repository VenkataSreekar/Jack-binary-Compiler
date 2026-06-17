import sys
import os


# ─────────────────────────────────────────────────────────────────────────────
# SymbolTable
# ─────────────────────────────────────────────────────────────────────────────

class SymbolTable:

    PREDEFINED = {
        "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
        "R0": 0,  "R1": 1,  "R2": 2,  "R3": 3,
        "R4": 4,  "R5": 5,  "R6": 6,  "R7": 7,
        "R8": 8,  "R9": 9,  "R10": 10, "R11": 11,
        "R12": 12, "R13": 13, "R14": 14, "R15": 15,
        "SCREEN": 16384, "KBD": 24576,
    }

    def __init__(self):
        self._table = dict(self.PREDEFINED)

    def add_entry(self, symbol: str, address: int) -> None:
        self._table[symbol] = address

    def contains(self, symbol: str) -> bool:
        return symbol in self._table

    def get_address(self, symbol: str) -> int:
        return self._table[symbol]


# ─────────────────────────────────────────────────────────────────────────────
# Parser
# ─────────────────────────────────────────────────────────────────────────────

class Parser:

    A_INSTRUCTION = "A_INSTRUCTION"
    C_INSTRUCTION = "C_INSTRUCTION"
    L_INSTRUCTION = "L_INSTRUCTION"

    def __init__(self, filename: str):
        with open(filename) as fh:
            raw = fh.readlines()
        self._lines = []
        for line in raw:
            line = line.split("//")[0].strip()
            if line:
                self._lines.append(line)
        self._index = -1
        self._current = None

    def has_more_lines(self) -> bool:
        return self._index < len(self._lines) - 1

    def advance(self) -> None:
        self._index += 1
        self._current = self._lines[self._index]

    def instruction_type(self) -> str:
        if self._current.startswith("@"):
            return self.A_INSTRUCTION
        if self._current.startswith("("):
            return self.L_INSTRUCTION
        return self.C_INSTRUCTION

    def symbol(self) -> str:
        t = self.instruction_type()
        if t == self.A_INSTRUCTION:
            return self._current[1:]
        if t == self.L_INSTRUCTION:
            return self._current[1:-1]
        raise ValueError("symbol() called on C-instruction")

    def dest(self) -> str:
        if "=" in self._current:
            return self._current.split("=")[0]
        return ""

    def comp(self) -> str:
        c = self._current
        if "=" in c:
            c = c.split("=")[1]
        if ";" in c:
            c = c.split(";")[0]
        return c

    def jump(self) -> str:
        if ";" in self._current:
            return self._current.split(";")[1]
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# Code
# ─────────────────────────────────────────────────────────────────────────────

class Code:

    _DEST = {
        "":    "000",
        "M":   "001",
        "D":   "010",
        "MD":  "011",
        "A":   "100",
        "AM":  "101",
        "AD":  "110",
        "AMD": "111",
    }

    _JUMP = {
        "":    "000",
        "JGT": "001",
        "JEQ": "010",
        "JGE": "011",
        "JLT": "100",
        "JNE": "101",
        "JLE": "110",
        "JMP": "111",
    }

    _COMP = {
        "0":   "0101010",
        "1":   "0111111",
        "-1":  "0111010",
        "D":   "0001100",
        "A":   "0110000",
        "!D":  "0001101",
        "!A":  "0110001",
        "-D":  "0001111",
        "-A":  "0110011",
        "D+1": "0011111",
        "A+1": "0110111",
        "D-1": "0001110",
        "A-1": "0110010",
        "D+A": "0000010",
        "D-A": "0010011",
        "A-D": "0000111",
        "D&A": "0000000",
        "D|A": "0010101",
        "M":   "1110000",
        "!M":  "1110001",
        "-M":  "1110011",
        "M+1": "1110111",
        "M-1": "1110010",
        "D+M": "1000010",
        "D-M": "1010011",
        "M-D": "1000111",
        "D&M": "1000000",
        "D|M": "1010101",
    }

    @classmethod
    def dest(cls, mnemonic: str) -> str:
        return cls._DEST[mnemonic]

    @classmethod
    def comp(cls, mnemonic: str) -> str:
        return cls._COMP[mnemonic]

    @classmethod
    def jump(cls, mnemonic: str) -> str:
        return cls._JUMP[mnemonic]


# ─────────────────────────────────────────────────────────────────────────────
# Assembler  (two-pass driver)
# ─────────────────────────────────────────────────────────────────────────────

class Assembler:

    VAR_BASE = 16

    def __init__(self, source_path: str):
        self._source = source_path
        base = os.path.splitext(source_path)[0]
        self._dest = base + ".hack"
        self._table = SymbolTable()

    def _first_pass(self) -> None:
        parser = Parser(self._source)
        rom_address = 0
        while parser.has_more_lines():
            parser.advance()
            t = parser.instruction_type()
            if t == Parser.L_INSTRUCTION:
                self._table.add_entry(parser.symbol(), rom_address)
            else:
                rom_address += 1

    def _second_pass(self) -> list[str]:
        parser = Parser(self._source)
        output = []
        var_address = self.VAR_BASE

        while parser.has_more_lines():
            parser.advance()
            t = parser.instruction_type()

            if t == Parser.L_INSTRUCTION:
                continue

            elif t == Parser.A_INSTRUCTION:
                sym = parser.symbol()
                if sym.isdigit():
                    value = int(sym)
                elif self._table.contains(sym):
                    value = self._table.get_address(sym)
                else:
                    self._table.add_entry(sym, var_address)
                    value = var_address
                    var_address += 1
                output.append(f"{value:016b}")

            else:
                comp_bits = Code.comp(parser.comp())
                dest_bits = Code.dest(parser.dest())
                jump_bits = Code.jump(parser.jump())
                output.append(f"111{comp_bits}{dest_bits}{jump_bits}")

        return output

    def assemble(self) -> None:
        self._first_pass()
        binary_lines = self._second_pass()
        with open(self._dest, "w") as fh:
            fh.write("\n".join(binary_lines) + "\n")
        print(f"Assembled {len(binary_lines)} instructions --> {self._dest}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python assembler.py <file.asm>")
        sys.exit(1)
    Assembler(sys.argv[1]).assemble()