import sys
if "" not in sys.path : sys.path.append("")
if "src" not in sys.path : sys.path.append("src")

import os
import warnings
from util.style import print_header


def preprocessing(paths, settings, verbose=True):
    """
    This function is the main function for the preprocessing step.
    It calls on other functions to perform some tasks, such as:
    - DICOM - NIFTI conversion
    - File structure management
    """

    if verbose : print_header("\n==== MODULE 1 - PREPROCESSING ====")

    if verbose : print_header("\nPREPROCESSING FINISHED")

    return


if __name__ == "__main__":
    preprocessing(..., ...)