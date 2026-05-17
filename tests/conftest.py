import sys
import os

# Ensure the project root and src directory are on sys.path
# so tests can import project modules (fund_tools package lives under src/)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, "src"))
