"""
VMWriter.py
"""


class VMWriter:
    _ARITHMETIC_CMDS = {
        "add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"
    }

    def __init__(self, output_path):
        self._path = output_path
        self.file  = open(output_path, 'w')

    # ------------------------------------------------------------------
    # Stack operations
    # ------------------------------------------------------------------
    def write_push(self, segment, index):
        """push <segment> <index>"""
        self.file.write(f"push {segment} {index}\n")

    def write_pop(self, segment, index):
        """pop <segment> <index>"""
        self.file.write(f"pop {segment} {index}\n")

    # ------------------------------------------------------------------
    # Arithmetic / logical
    # ------------------------------------------------------------------
    def write_arithmetic(self, command):
        """
        command must be one of:
            add sub neg eq gt lt and or not
        """
        cmd = command.strip().lower()
        if cmd not in self._ARITHMETIC_CMDS:
            raise ValueError(f"VMWriter: unknown arithmetic command '{command}'")
        self.file.write(f"{cmd}\n")

    # ------------------------------------------------------------------
    # Branching
    # ------------------------------------------------------------------
    def write_label(self, label):
        self.file.write(f"label {label}\n")

    def write_goto(self, label):
        self.file.write(f"goto {label}\n")

    def write_if(self, label):
        self.file.write(f"if-goto {label}\n")

    # ------------------------------------------------------------------
    # Functions
    # ------------------------------------------------------------------
    def write_call(self, name, n_args):
        self.file.write(f"call {name} {n_args}\n")

    def write_function(self, name, n_locals):
        self.file.write(f"function {name} {n_locals}\n")

    def write_return(self):
        self.file.write("return\n")

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def write_comment(self, text):
        """Emit a VM comment line (stripped by most VM translators but handy for debugging)."""
        self.file.write(f"// {text}\n")

    def close(self):
        if not self.file.closed:
            self.file.close()

    # Context-manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False   # do not suppress exceptions
