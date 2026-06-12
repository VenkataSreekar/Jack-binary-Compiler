import os

class Parser:
    C_ARITHMETIC = "C_ARITHMETIC"
    C_PUSH = "C_PUSH"
    C_POP = "C_POP"
    C_LABEL = "C_LABEL"
    C_GOTO = "C_GOTO"
    C_IF = "C_IF"
    C_FUNCTION = "C_FUNCTION"
    C_RETURN = "C_RETURN"
    C_CALL = "C_CALL"

    def __init__(self, file_path):
        with open(file_path, 'r') as f:
            self.lines = [line.split('//')[0].strip() for line in f.readlines()]
            self.lines = [line for line in self.lines if line]
        
        self.current_command = None
        self.current_index = -1
        self.arithmetic_commands = {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}

    def has_more_commands(self):
        return self.current_index + 1 < len(self.lines)

    def advance(self):
        self.current_index += 1
        self.current_command = self.lines[self.current_index].split()

    def command_type(self):
        cmd = self.current_command[0]
        if cmd in self.arithmetic_commands: return self.C_ARITHMETIC
        if cmd == "push": return self.C_PUSH
        if cmd == "pop": return self.C_POP
        if cmd == "label": return self.C_LABEL
        if cmd == "goto": return self.C_GOTO
        if cmd == "if-goto": return self.C_IF
        if cmd == "function": return self.C_FUNCTION
        if cmd == "return": return self.C_RETURN
        if cmd == "call": return self.C_CALL
        
        raise ValueError(f"Syntax Error: Unknown VM command '{cmd}' on line {self.current_index + 1}")

    def arg1(self):
        if self.command_type() == self.C_ARITHMETIC:
            return self.current_command[0]
        return self.current_command[1]

    def arg2(self):
        if len(self.current_command) > 2:
            return int(self.current_command[2])
        raise IndexError(f"Syntax Error: Command '{self.current_command[0]}' is missing its numeric argument.")


class CodeWriter:
    def __init__(self, output_file):
        self.file = open(output_file, 'w')
        self.filename = ""
        self.label_counter = 0
        self.call_counter = 0
        self.current_function = ""
        
        self.segments = {
            "local": "LCL", "argument": "ARG", "this": "THIS", "that": "THAT"
        }

    def set_file_name(self, filename):
        self.filename = os.path.basename(filename).replace('.vm', '')

    def write_init(self):
        self.file.write("// Bootstrap code\n")
        self.file.write("@256\nD=A\n@SP\nM=D\n")
        self.write_call("Sys.init", 0)

    def _get_new_label(self, prefix):
        self.label_counter += 1
        return f"{prefix}_{self.label_counter}"

    def write_arithmetic(self, command):
        self.file.write(f"// {command}\n")
        
        if command in ["add", "sub", "and", "or"]:
            self.file.write("@SP\nAM=M-1\nD=M\nA=A-1\n")
            if command == "add": self.file.write("M=M+D\n")
            elif command == "sub": self.file.write("M=M-D\n")
            elif command == "and": self.file.write("M=M&D\n")
            elif command == "or": self.file.write("M=M|D\n")
            
        elif command in ["neg", "not"]:
            self.file.write("@SP\nA=M-1\n")
            if command == "neg": self.file.write("M=-M\n")
            elif command == "not": self.file.write("M=!M\n")
            
        elif command in ["eq", "gt", "lt"]:
            l_true = self._get_new_label("TRUE")
            l_end = self._get_new_label("END")
            jump_cmd = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}[command]
            
            self.file.write("@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\n")
            self.file.write(f"@{l_true}\nD;{jump_cmd}\n")
            self.file.write("@SP\nA=M-1\nM=0\n")
            self.file.write(f"@{l_end}\n0;JMP\n")
            self.file.write(f"({l_true})\n@SP\nA=M-1\nM=-1\n")
            self.file.write(f"({l_end})\n")

    def write_push_pop(self, command, segment, index):
        self.file.write(f"// {command} {segment} {index}\n")
        
        if command == Parser.C_PUSH:
            if segment == "constant":
                self.file.write(f"@{index}\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
            elif segment in self.segments:
                self.file.write(f"@{index}\nD=A\n@{self.segments[segment]}\nA=M+D\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
            elif segment == "temp":
                self.file.write(f"@{5 + index}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
            elif segment == "pointer":
                base = "THIS" if index == 0 else "THAT"
                self.file.write(f"@{base}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
            elif segment == "static":
                self.file.write(f"@{self.filename}.{index}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
                
        elif command == Parser.C_POP:
            if segment in self.segments:
                self.file.write(f"@{index}\nD=A\n@{self.segments[segment]}\nD=M+D\n@R13\nM=D\n@SP\nAM=M-1\nD=M\n@R13\nA=M\nM=D\n")
            elif segment == "temp":
                self.file.write(f"@SP\nAM=M-1\nD=M\n@{5 + index}\nM=D\n")
            elif segment == "pointer":
                base = "THIS" if index == 0 else "THAT"
                self.file.write(f"@SP\nAM=M-1\nD=M\n@{base}\nM=D\n")
            elif segment == "static":
                self.file.write(f"@SP\nAM=M-1\nD=M\n@{self.filename}.{index}\nM=D\n")

    def write_label(self, label):
        scoped_label = f"{self.current_function}${label}" if self.current_function else label
        self.file.write(f"({scoped_label})\n")

    def write_goto(self, label):
        scoped_label = f"{self.current_function}${label}" if self.current_function else label
        self.file.write(f"@{scoped_label}\n0;JMP\n")

    def write_if(self, label):
        scoped_label = f"{self.current_function}${label}" if self.current_function else label
        self.file.write(f"@SP\nAM=M-1\nD=M\n@{scoped_label}\nD;JNE\n")

    def write_call(self, function_name, num_args):
        return_label = f"{function_name}_RETURN_{self.call_counter}"
        self.call_counter += 1
        
        self.file.write(f"@{return_label}\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
        for reg in ["LCL", "ARG", "THIS", "THAT"]:
            self.file.write(f"@{reg}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
            
        self.file.write(f"@SP\nD=M\n@{num_args}\nD=D-A\n@5\nD=D-A\n@ARG\nM=D\n")
        self.file.write("@SP\nD=M\n@LCL\nM=D\n")
        
        self.file.write(f"@{function_name}\n0;JMP\n")
        self.file.write(f"({return_label})\n")

    def write_return(self):
        self.file.write("@LCL\nD=M\n@R14\nM=D\n")
        self.file.write("@5\nA=D-A\nD=M\n@R15\nM=D\n")
        self.file.write("@SP\nAM=M-1\nD=M\n@ARG\nA=M\nM=D\n")
        self.file.write("@ARG\nD=M+1\n@SP\nM=D\n")
        
        for i, reg in enumerate(["THAT", "THIS", "ARG", "LCL"], 1):
            self.file.write(f"@R14\nD=M\n@{i}\nA=D-A\nD=M\n@{reg}\nM=D\n")
            
        self.file.write("@R15\nA=M\n0;JMP\n")

    def write_function(self, function_name, num_locals):
        self.current_function = function_name
        self.file.write(f"({function_name})\n")
        for _ in range(num_locals):
            self.write_push_pop(Parser.C_PUSH, "constant", 0)

    def close(self):
        self.file.close()