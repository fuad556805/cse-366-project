"""
conftest.py

Kaj: pytest run korar somoy "core" folder-ke Python path-e
jog kore deya, jate test file gula theke shorashori
`from dataset_loader import ...` ei rokom import kora jay.
"""

import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE_DIR = os.path.join(ROOT_DIR, "core")

sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, CORE_DIR)
