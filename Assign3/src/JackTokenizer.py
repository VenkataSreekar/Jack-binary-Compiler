"""
JackTokenizer.py
"""

import re
import os


class JackTokenizer:
    KEYWORDS = {
        "class", "constructor", "function", "method", "field", "static",
        "var", "int", "char", "boolean", "void", "true", "false", "null",
        "this", "let", "do", "if", "else", "while", "return"
    }
    SYMBOLS = set('{}()[].,;+-*/&|<>=~')

    # Token regex — order matters: strings first, then symbols, then words/ints
    _TOKEN_RE = re.compile(
        r'"[^"\n]*"'          # string constant  (group captures quotes)
        r'|[{}()\[\].,;+\-*/&|<>=~]'  # symbol
        r'|\d+'               # integer constant
        r'|[A-Za-z_]\w*'      # identifier or keyword
    )

    def __init__(self, input_path):
        with open(input_path, 'r') as f:
            raw = f.read()
        self._clean = self._strip_comments(raw)
        self.tokens = self._tokenize(self._clean)
        self.current_token_idx = 0

    # ------------------------------------------------------------------
    # Comment removal
    # ------------------------------------------------------------------
    @staticmethod
    def _strip_comments(text):
        # Block comments /** ... */ and /* ... */ (including multi-line)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        # Single-line comments
        text = re.sub(r'//[^\n]*', '', text)
        return text

    # ------------------------------------------------------------------
    # Tokenisation
    # ------------------------------------------------------------------
    def _tokenize(self, text):
        tokens = []
        for m in self._TOKEN_RE.finditer(text):
            raw = m.group(0)

            if raw.startswith('"'):
                # string constant — strip surrounding quotes
                tokens.append(("stringConstant", raw[1:-1]))
            elif raw in self.SYMBOLS:
                tokens.append(("symbol", raw))
            elif raw.isdigit() or (raw[0].isdigit()):
                # multi-digit integers are fully captured by \d+
                tokens.append(("integerConstant", raw))
            elif raw in self.KEYWORDS:
                tokens.append(("keyword", raw))
            else:
                tokens.append(("identifier", raw))
        return tokens

    # ------------------------------------------------------------------
    # Public navigation API (used by CompilationEngine)
    # ------------------------------------------------------------------
    def has_more_tokens(self):
        return self.current_token_idx < len(self.tokens)

    def advance(self):
        if self.has_more_tokens():
            self.current_token_idx += 1

    def current_token(self):
        if self.has_more_tokens():
            return self.tokens[self.current_token_idx]
        return None

    def peek(self, offset=1):
        """Look ahead without consuming tokens."""
        idx = self.current_token_idx + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None

    # ------------------------------------------------------------------
    # Pipeline entry point (called by JackCompiler)
    # ------------------------------------------------------------------
    def tokenize(self):
        """Return the full token list and write <stem>T.xml as a side-effect."""
        return self.tokens

    # ------------------------------------------------------------------
    # XML export
    # ------------------------------------------------------------------
    @staticmethod
    def _xml_escape(value):
        """Escape every XML-unsafe character in value."""
        value = value.replace('&', '&amp;')   # must be first
        value = value.replace('<', '&lt;')
        value = value.replace('>', '&gt;')
        value = value.replace('"', '&quot;')
        return value

    def export_xml(self, output_path):
        """Write <ClassName>T.xml."""
        with open(output_path, 'w') as f:
            f.write("<tokens>\n")
            for token_type, value in self.tokens:
                safe = self._xml_escape(value)
                f.write(f"<{token_type}> {safe} </{token_type}>\n")
            f.write("</tokens>\n")

    # kept for backward compatibility
    def get_all_tokens(self):
        return self.tokens
