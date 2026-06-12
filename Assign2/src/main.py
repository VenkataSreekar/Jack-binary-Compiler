import sys
import os
from HackVM import Parser, CodeWriter

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <file.vm or directory>")
        sys.exit(1)

    input_path = sys.argv[1]
    
    is_dir = os.path.isdir(input_path)
    if is_dir:
        vm_files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith('.vm')]
        output_file = os.path.join(input_path, os.path.basename(os.path.normpath(input_path)) + ".asm")
    else:
        vm_files = [input_path]
        output_file = input_path.replace(".vm", ".asm")

    writer = CodeWriter(output_file)
    
    if is_dir:
        writer.write_init()

    for vm_file in vm_files:
        writer.set_file_name(vm_file)
        parser = Parser(vm_file)
        
        writer.current_function = ""
        
        while parser.has_more_commands():
            parser.advance()
            cmd_type = parser.command_type()
            
            if cmd_type == Parser.C_ARITHMETIC:
                writer.write_arithmetic(parser.arg1())
            elif cmd_type in [Parser.C_PUSH, Parser.C_POP]:
                writer.write_push_pop(cmd_type, parser.arg1(), parser.arg2())
            elif cmd_type == Parser.C_LABEL:
                writer.write_label(parser.arg1())
            elif cmd_type == Parser.C_GOTO:
                writer.write_goto(parser.arg1())
            elif cmd_type == Parser.C_IF:
                writer.write_if(parser.arg1())
            elif cmd_type == Parser.C_FUNCTION:
                writer.write_function(parser.arg1(), parser.arg2())
            elif cmd_type == Parser.C_RETURN:
                writer.write_return()
            elif cmd_type == Parser.C_CALL:
                writer.write_call(parser.arg1(), parser.arg2())

    writer.close()
    print(f"Translation complete. Output saved to: {output_file}")

if __name__ == "__main__":
    main()