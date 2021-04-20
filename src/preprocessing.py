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

    # Check whether module should be run (from config file)
    if settings["run_modules"][1] == 0:
        if verbose : print("Skipped module...")
    elif settings["run_modules"][1] == 1:   
        # TODO: Implement preprocessing
        if verbose : print_header("\nPREPROCESSING FINISHED")
        return
    else:
        raise ValueError("parameter run_modules should be a list containing only 0's and 1's. " \
                        "Please check the config file (config.json).")


if __name__ == "__main__":
    preprocessing(..., ...)