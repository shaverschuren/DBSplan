"""DBSplan - Path Planning module

This module performs several tasks, which may all
be called from the `path_planning` function.
- ...
- ...
"""

# Path setup
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(root, "src")
if root not in sys.path: sys.path.append(root)
if src not in sys.path: sys.path.append(src)

# File-specific imports
import numpy as np              # noqa: E402


def path_planning(paths, settings):
    """
    This is the main wrapper function for the path planning module.
    It calls on other functions to perform specific tasks.
    """

    return
