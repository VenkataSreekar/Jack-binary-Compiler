"""
CompilationEngine.py
"""

import os
from SymbolTable import SymbolTable
from VMWriter    import VMWriter


class CompilationEngine:
    # Jack binary/unary operators
    _BINARY_OPS  = {'+', '-', '*', '/', '&', '|', '<', '>', '='}
    _UNARY_OPS   = {'-', '~'}

    # Map Jack binary op → VM command (or special call)
    _OP_TO_VM = {
        '+': 'add', '-': 'sub', '&': 'and', '|': 'or',
        '<': 'lt',  '>': 'gt',  '=': 'eq',
        '*': 'Math.multiply',   '/': 'Math.divide',
    }

    def __init__(self, tokens, xml_output_path, vm_output_path):
        """
        tokens          : list of (type, value) from JackTokenizer
        xml_output_path : where to write the parse-tree XML
        vm_output_path  : where to write the VM code
        """
        self._tokens  = tokens
        self._pos     = 0                      # current token index
        self._xml     = open(xml_output_path, 'w')
        self._vm      = VMWriter(vm_output_path)
        self._sym     = SymbolTable()
        self._indent  = 0                      # XML indentation level
        self._class_name   = ""
        self._label_count  = 0                 # for generating unique labels

    # ==================================================================
    # Token navigation helpers
    # ==================================================================

    def _current(self):
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _peek(self, offset=1):
        idx = self._pos + offset
        if idx < len(self._tokens):
            return self._tokens[idx]
        return None

    def _advance(self):
        tok = self._current()
        self._pos += 1
        return tok

    def _expect(self, expected_type=None, expected_value=None):
        """Consume the current token, asserting its type and/or value."""
        tok = self._current()
        if tok is None:
            raise SyntaxError(f"Unexpected end of tokens; expected {expected_type} '{expected_value}'")
        t_type, t_val = tok
        if expected_type and t_type != expected_type:
            raise SyntaxError(f"Expected token type '{expected_type}' but got '{t_type}' ('{t_val}')")
        if expected_value and t_val != expected_value:
            raise SyntaxError(f"Expected '{expected_value}' but got '{t_val}'")
        self._write_xml_token(t_type, t_val)
        self._advance()
        return t_val

    # ==================================================================
    # XML helpers
    # ==================================================================

    @staticmethod
    def _xml_escape(v):
        v = v.replace('&', '&amp;')
        v = v.replace('<', '&lt;')
        v = v.replace('>', '&gt;')
        v = v.replace('"', '&quot;')
        return v

    def _write_xml_token(self, tok_type, value):
        pad = "  " * self._indent
        safe = self._xml_escape(value)
        self._xml.write(f"{pad}<{tok_type}> {safe} </{tok_type}>\n")

    def _xml_open(self, tag):
        self._xml.write("  " * self._indent + f"<{tag}>\n")
        self._indent += 1

    def _xml_close(self, tag):
        self._indent -= 1
        self._xml.write("  " * self._indent + f"</{tag}>\n")

    # ==================================================================
    # Label generator
    # ==================================================================

    def _new_label(self, prefix="L"):
        lbl = f"{self._class_name}_{prefix}_{self._label_count}"
        self._label_count += 1
        return lbl

    # ==================================================================
    # compile_class  (top-level entry point)
    # ==================================================================

    def compile_class(self):
        """class className '{' classVarDec* subroutineDec* '}'"""
        self._xml_open("class")

        self._expect("keyword", "class")
        self._class_name = self._expect("identifier")   # className
        self._expect("symbol", "{")

        # classVarDec*
        while self._current() and self._current()[1] in ("static", "field"):
            self.compile_class_var_dec()

        # subroutineDec*
        while self._current() and self._current()[1] in ("constructor", "function", "method"):
            self.compile_subroutine()

        self._expect("symbol", "}")
        self._xml_close("class")
        self.close()

    # ==================================================================
    # classVarDec
    # ==================================================================

    def compile_class_var_dec(self):
        """('static'|'field') type varName (',' varName)* ';'"""
        self._xml_open("classVarDec")

        kind     = self._expect("keyword")          # static | field
        var_type = self._compile_type()             # int | char | boolean | className
        name     = self._expect("identifier")
        self._sym.define(name, var_type, kind)

        while self._current() and self._current()[1] == ',':
            self._expect("symbol", ",")
            name = self._expect("identifier")
            self._sym.define(name, var_type, kind)

        self._expect("symbol", ";")
        self._xml_close("classVarDec")

    # ==================================================================
    # subroutineDec
    # ==================================================================

    def compile_subroutine(self):
        """
        ('constructor'|'function'|'method') ('void'|type) subroutineName
        '(' parameterList ')' subroutineBody
        """
        self._xml_open("subroutineDec")
        self._sym.start_subroutine()

        sub_type  = self._expect("keyword")            # constructor/function/method
        self._compile_type(allow_void=True)            # return type
        sub_name  = self._expect("identifier")         # subroutineName

        # For methods, the first argument is always 'this'
        if sub_type == "method":
            self._sym.define("this", self._class_name, "arg")

        self._expect("symbol", "(")
        self.compile_parameter_list()
        self._expect("symbol", ")")

        # subroutineBody
        self._xml_open("subroutineBody")
        self._expect("symbol", "{")

        # varDec*  — must be compiled before we can emit the function declaration
        # because we need to know n_locals first; buffer the var declarations.
        while self._current() and self._current()[1] == "var":
            self.compile_var_dec()

        n_locals = self._sym.var_count("var")
        fn_full  = f"{self._class_name}.{sub_name}"
        self._vm.write_function(fn_full, n_locals)

        # Set up 'this' pointer depending on subroutine type
        if sub_type == "constructor":
            n_fields = self._sym.var_count("field")
            self._vm.write_push("constant", n_fields)
            self._vm.write_call("Memory.alloc", 1)
            self._vm.write_pop("pointer", 0)
        elif sub_type == "method":
            self._vm.write_push("argument", 0)
            self._vm.write_pop("pointer", 0)

        # statements
        self.compile_statements()

        self._expect("symbol", "}")
        self._xml_close("subroutineBody")
        self._xml_close("subroutineDec")

    # ==================================================================
    # parameterList
    # ==================================================================

    def compile_parameter_list(self):
        """((type varName) (',' type varName)*)?"""
        self._xml_open("parameterList")

        if self._current() and self._current()[1] != ')':
            var_type = self._compile_type()
            name     = self._expect("identifier")
            self._sym.define(name, var_type, "arg")

            while self._current() and self._current()[1] == ',':
                self._expect("symbol", ",")
                var_type = self._compile_type()
                name     = self._expect("identifier")
                self._sym.define(name, var_type, "arg")

        self._xml_close("parameterList")

    # ==================================================================
    # varDec
    # ==================================================================

    def compile_var_dec(self):
        """'var' type varName (',' varName)* ';'"""
        self._xml_open("varDec")

        self._expect("keyword", "var")
        var_type = self._compile_type()
        name     = self._expect("identifier")
        self._sym.define(name, var_type, "var")

        while self._current() and self._current()[1] == ',':
            self._expect("symbol", ",")
            name = self._expect("identifier")
            self._sym.define(name, var_type, "var")

        self._expect("symbol", ";")
        self._xml_close("varDec")

    # ==================================================================
    # statements
    # ==================================================================

    def compile_statements(self):
        """statement*"""
        self._xml_open("statements")

        dispatch = {
            "let":    self.compile_let,
            "if":     self.compile_if,
            "while":  self.compile_while,
            "do":     self.compile_do,
            "return": self.compile_return,
        }
        while self._current() and self._current()[1] in dispatch:
            dispatch[self._current()[1]]()

        self._xml_close("statements")

    # ==================================================================
    # letStatement
    # ==================================================================

    def compile_let(self):
        """'let' varName ('[' expression ']')? '=' expression ';'"""
        self._xml_open("letStatement")

        self._expect("keyword", "let")
        var_name  = self._expect("identifier")
        segment   = self._sym.kind_of(var_name)
        idx       = self._sym.index_of(var_name)
        is_array  = False

        if self._current() and self._current()[1] == '[':
            # Array assignment: push base address, compile index, add
            is_array = True
            self._vm.write_push(segment, idx)
            self._expect("symbol", "[")
            self.compile_expression()
            self._expect("symbol", "]")
            self._vm.write_arithmetic("add")   # base + index → on stack

        self._expect("symbol", "=")
        self.compile_expression()              # RHS value on stack
        self._expect("symbol", ";")

        if is_array:
            # pointer 1 / that 0 idiom:
            # stack: [target_addr, rhs_value]
            self._vm.write_pop("temp", 0)      # save RHS
            self._vm.write_pop("pointer", 1)   # set THAT to target address
            self._vm.write_push("temp", 0)     # restore RHS
            self._vm.write_pop("that", 0)      # store into RAM[THAT+0]
        else:
            self._vm.write_pop(segment, idx)

        self._xml_close("letStatement")

    # ==================================================================
    # ifStatement
    # ==================================================================

    def compile_if(self):
        """'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?"""
        self._xml_open("ifStatement")

        label_true  = self._new_label("IF_TRUE")
        label_false = self._new_label("IF_FALSE")
        label_end   = self._new_label("IF_END")

        self._expect("keyword", "if")
        self._expect("symbol", "(")
        self.compile_expression()
        self._expect("symbol", ")")

        self._vm.write_if(label_true)
        self._vm.write_goto(label_false)
        self._vm.write_label(label_true)

        self._expect("symbol", "{")
        self.compile_statements()
        self._expect("symbol", "}")

        if self._current() and self._current()[1] == "else":
            self._vm.write_goto(label_end)
            self._vm.write_label(label_false)
            self._expect("keyword", "else")
            self._expect("symbol", "{")
            self.compile_statements()
            self._expect("symbol", "}")
            self._vm.write_label(label_end)
        else:
            self._vm.write_label(label_false)

        self._xml_close("ifStatement")

    # ==================================================================
    # whileStatement
    # ==================================================================

    def compile_while(self):
        """'while' '(' expression ')' '{' statements '}'"""
        self._xml_open("whileStatement")

        label_start = self._new_label("WHILE_START")
        label_end   = self._new_label("WHILE_END")

        self._vm.write_label(label_start)

        self._expect("keyword", "while")
        self._expect("symbol", "(")
        self.compile_expression()
        self._expect("symbol", ")")

        self._vm.write_arithmetic("not")
        self._vm.write_if(label_end)

        self._expect("symbol", "{")
        self.compile_statements()
        self._expect("symbol", "}")

        self._vm.write_goto(label_start)
        self._vm.write_label(label_end)

        self._xml_close("whileStatement")

    # ==================================================================
    # doStatement
    # ==================================================================

    def compile_do(self):
        """'do' subroutineCall ';'"""
        self._xml_open("doStatement")

        self._expect("keyword", "do")
        # subroutineCall: identifier ('.' identifier)? '(' expressionList ')'
        name = self._expect("identifier")
        self._compile_subroutine_call(name)
        self._expect("symbol", ";")

        # discard the return value (do-statements ignore it)
        self._vm.write_pop("temp", 0)

        self._xml_close("doStatement")

    # ==================================================================
    # returnStatement
    # ==================================================================

    def compile_return(self):
        """'return' expression? ';'"""
        self._xml_open("returnStatement")

        self._expect("keyword", "return")

        if self._current() and self._current()[1] != ';':
            self.compile_expression()
        else:
            # void return — push dummy 0
            self._vm.write_push("constant", 0)

        self._expect("symbol", ";")
        self._vm.write_return()

        self._xml_close("returnStatement")

    # ==================================================================
    # expression
    # ==================================================================

    def compile_expression(self):
        """term (op term)*"""
        self._xml_open("expression")

        self.compile_term()
        while self._current() and self._current()[1] in self._BINARY_OPS:
            op = self._expect("symbol")
            self.compile_term()
            # emit VM operation after both operands are on the stack
            vm_op = self._OP_TO_VM[op]
            if '.' in vm_op:
                self._vm.write_call(vm_op, 2)   # Math.multiply / Math.divide
            else:
                self._vm.write_arithmetic(vm_op)

        self._xml_close("expression")

    # ==================================================================
    # term
    # ==================================================================

    def compile_term(self):
        """
        integerConstant | stringConstant | keywordConstant |
        varName | varName '[' expression ']' |
        subroutineCall | '(' expression ')' | unaryOp term
        """
        self._xml_open("term")

        tok = self._current()
        if tok is None:
            self._xml_close("term")
            return

        t_type, t_val = tok

        # --- integer constant ---
        if t_type == "integerConstant":
            self._expect("integerConstant")
            self._vm.write_push("constant", int(t_val))

        # --- string constant ---
        elif t_type == "stringConstant":
            self._expect("stringConstant")
            # Allocate a String object and append each character
            self._vm.write_push("constant", len(t_val))
            self._vm.write_call("String.new", 1)
            for ch in t_val:
                self._vm.write_push("constant", ord(ch))
                self._vm.write_call("String.appendChar", 2)

        # --- keyword constants ---
        elif t_type == "keyword" and t_val in ("true", "false", "null", "this"):
            self._expect("keyword")
            if t_val == "true":
                self._vm.write_push("constant", 0)
                self._vm.write_arithmetic("not")
            elif t_val in ("false", "null"):
                self._vm.write_push("constant", 0)
            else:  # this
                self._vm.write_push("pointer", 0)

        # --- grouped expression ---
        elif t_type == "symbol" and t_val == '(':
            self._expect("symbol", "(")
            self.compile_expression()
            self._expect("symbol", ")")

        # --- unary operator ---
        elif t_type == "symbol" and t_val in self._UNARY_OPS:
            op = self._expect("symbol")
            self.compile_term()
            self._vm.write_arithmetic("neg" if op == '-' else "not")

        # --- identifier: varName, varName[expr], or subroutineCall ---
        elif t_type == "identifier":
            name = self._expect("identifier")
            nxt  = self._current()

            if nxt and nxt[1] == '[':
                # varName '[' expression ']'
                segment = self._sym.kind_of(name)
                idx     = self._sym.index_of(name)
                self._vm.write_push(segment, idx)
                self._expect("symbol", "[")
                self.compile_expression()
                self._expect("symbol", "]")
                self._vm.write_arithmetic("add")
                self._vm.write_pop("pointer", 1)
                self._vm.write_push("that", 0)

            elif nxt and nxt[1] in ('.', '('):
                # subroutineCall
                self._compile_subroutine_call(name)

            else:
                # plain varName
                segment = self._sym.kind_of(name)
                idx     = self._sym.index_of(name)
                self._vm.write_push(segment, idx)

        self._xml_close("term")

    # ==================================================================
    # expressionList
    # ==================================================================

    def compile_expression_list(self):
        """(expression (',' expression)*)?   → returns n_args"""
        self._xml_open("expressionList")
        n_args = 0

        if self._current() and self._current()[1] != ')':
            self.compile_expression()
            n_args = 1
            while self._current() and self._current()[1] == ',':
                self._expect("symbol", ",")
                self.compile_expression()
                n_args += 1

        self._xml_close("expressionList")
        return n_args

    # ==================================================================
    # Internal helpers
    # ==================================================================

    def _compile_type(self, allow_void=False):
        """
        type: 'int' | 'char' | 'boolean' | className
        Consume and return the type token value.
        """
        tok = self._current()
        if tok is None:
            raise SyntaxError("Expected type but got end of tokens")
        t_type, t_val = tok
        primitives = {"int", "char", "boolean"}
        if allow_void:
            primitives.add("void")
        if t_type == "keyword" and t_val in primitives:
            return self._expect("keyword")
        elif t_type == "identifier":
            return self._expect("identifier")
        else:
            raise SyntaxError(f"Expected type, got '{t_val}'")

    def _compile_subroutine_call(self, first_name):
        """
        Handle   firstName(args)
        or       firstName.subName(args)

        'first_name' has already been consumed by the caller.
        """
        n_args = 0
        tok = self._current()

        if tok and tok[1] == '.':
            # className.subroutineName(args)  OR  varName.method(args)
            self._expect("symbol", ".")
            sub_name = self._expect("identifier")

            # Determine whether first_name is a variable (method call) or a class name
            seg = self._sym.kind_of(first_name)
            if seg is not None:
                # It's a variable → method call → push the object as arg 0
                idx  = self._sym.index_of(first_name)
                cls  = self._sym.type_of(first_name)
                self._vm.write_push(seg, idx)
                n_args = 1
                full_name = f"{cls}.{sub_name}"
            else:
                # It's a class name → plain function/constructor call
                full_name = f"{first_name}.{sub_name}"

            self._expect("symbol", "(")
            n_args += self.compile_expression_list()
            self._expect("symbol", ")")

        else:
            # subroutineName(args) → method call on current object (this)
            self._vm.write_push("pointer", 0)    # push this
            n_args = 1
            full_name = f"{self._class_name}.{first_name}"
            self._expect("symbol", "(")
            n_args += self.compile_expression_list()
            self._expect("symbol", ")")

        self._vm.write_call(full_name, n_args)

    # ==================================================================
    # Cleanup
    # ==================================================================

    def close(self):
        self._xml.close()
        self._vm.close()
