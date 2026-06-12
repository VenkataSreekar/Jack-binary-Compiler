"""
SymbolTable.py
"""


class SymbolTable:
    # Maps internal kind name → VM memory segment
    KIND_TO_SEGMENT = {
        "static":   "static",
        "field":    "this",
        "arg":      "argument",
        "var":      "local",
    }

    def __init__(self):
        self.class_scope      = {}   # name → {type, kind, index}
        self.subroutine_scope = {}
        # Separate counters so class-level ones survive start_subroutine()
        self._class_counts     = {"static": 0, "field": 0}
        self._sub_counts       = {"arg": 0, "var": 0}

    # ------------------------------------------------------------------
    # Scope management
    # ------------------------------------------------------------------
    def start_subroutine(self):
        """Clear subroutine scope and reset arg/var counters only."""
        self.subroutine_scope.clear()
        self._sub_counts["arg"] = 0
        self._sub_counts["var"] = 0

    # ------------------------------------------------------------------
    # Define a new identifier
    # ------------------------------------------------------------------
    def define(self, name, sym_type, kind):
        """
        kind must be one of: "static", "field", "arg", "var"
        """
        if kind in ("static", "field"):
            idx = self._class_counts[kind]
            self.class_scope[name] = {"type": sym_type, "kind": kind, "index": idx}
            self._class_counts[kind] += 1
        elif kind in ("arg", "var"):
            idx = self._sub_counts[kind]
            self.subroutine_scope[name] = {"type": sym_type, "kind": kind, "index": idx}
            self._sub_counts[kind] += 1

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def var_count(self, kind):
        """Number of variables of the given kind already defined."""
        if kind in self._class_counts:
            return self._class_counts[kind]
        return self._sub_counts.get(kind, 0)

    def _lookup(self, name):
        """Return the entry dict for name, checking subroutine scope first."""
        if name in self.subroutine_scope:
            return self.subroutine_scope[name]
        if name in self.class_scope:
            return self.class_scope[name]
        return None

    def kind_of(self, name):
        """
        Return the VM segment string for name, or None if not found.
        "field"  → "this"
        "var"    → "local"
        "arg"    → "argument"
        "static" → "static"
        """
        entry = self._lookup(name)
        if entry is None:
            return None
        return self.KIND_TO_SEGMENT[entry["kind"]]

    def type_of(self, name):
        entry = self._lookup(name)
        return entry["type"] if entry else None

    def index_of(self, name):
        entry = self._lookup(name)
        return entry["index"] if entry else None
