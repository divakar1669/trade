import sys

# Must happen before any other imports that touch stdout
try:
    import colorama
    colorama.init()
except Exception:
    pass

try:
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from trade.cli import _splash, _repl, app

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        # No subcommand — interactive mode
        _splash()
        _repl()
    else:
        # Pass through to Typer for structured commands
        app()
