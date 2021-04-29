import sys
if "" not in sys.path: sys.path.append("")
if "src" not in sys.path: sys.path.append("src")

import subprocess
from initialization import initialization
from preprocessing import preprocessing
from segmentation import segmentation
from util.style import print_header


def registration(paths, settings, verbose=True):
    """
    This is the main wrapper function for the registration module.
    It calls on other functions to perform specific tasks.
    """

    if verbose: print_header("\n==== MODULE 3 - REGISTRATION ====")

    # Check whether module should be run (from config file)
    if settings["runModules"][2] == 0:
        # Skip module
        if verbose: print("\nSKIPPED:\n"
                          "'run_modules'[2] parameter == 0.\n"
                          "Assuming all data is already registered.\n"
                          "Skipping registration process. "
                          "Added expected nifti paths to 'paths'.")

    elif settings["runModules"][2] == 1:
        # Run module
        # TODO: Implement registration module

        if verbose: print_header("\nREGISTRATION FINISHED")

    else:
        raise ValueError("parameter run_modules should be a list "
                         "containing only 0's and 1's. "
                         "Please check the config file (config.json).")

    return paths, settings


if __name__ == "__main__":
    paths, settings = segmentation(*preprocessing(*initialization()))
    registration(paths, settings)
