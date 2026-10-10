"""Script to run Alembic migrations without namespace conflicts."""

import sys
import os

# Must be run from project root, not from backend/ which shadows 'alembic' package
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, backend_dir)

# Change to backend directory for alembic.ini resolution
os.chdir(backend_dir)

# Now import alembic from site-packages (not local dir) by using importlib
import importlib.util
import importlib.machinery

# Remove local alembic path from sys.modules to force reimport from site-packages
if "alembic" in sys.modules:
    del sys.modules["alembic"]

# Run alembic upgrade
from alembic.config import Config
from alembic import command

cfg = Config("alembic.ini")
cfg.set_main_option("script_location", "alembic")

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "upgrade"
    if action == "upgrade":
        command.upgrade(cfg, "head")
        print("Database upgraded to head successfully.")
    elif action == "downgrade":
        command.downgrade(cfg, "-1")
        print("Downgraded one revision.")
    elif action == "current":
        command.current(cfg)
    else:
        print(f"Unknown action: {action}")
