"""Alembic runner script — use instead of 'alembic' CLI when no alembic.exe is available."""

import sys
import os

# Add backend dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("PYTHONPATH", os.path.dirname(os.path.abspath(__file__)))

from alembic.config import Config, main as alembic_main

if __name__ == "__main__":
    alembic_main(prog="alembic")
