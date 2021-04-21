import sys
if "" not in sys.path : sys.path.append("")
if "src" not in sys.path : sys.path.append("src")

import subprocess
from initialization import initialization
from preprocessing import preprocessing
from util.style import print_header
from util.checks import check_freesurfer


def registration(paths, settings, verbose=True):
    """
    This is the main wrapper function for the registration module.
    It calls on other functions to perform specific tasks.
    """

    if verbose : print_header("\n==== MODULE 2 - REGISTRATION ====")

    # Check whether module should be run (from config file)
    if settings["run_modules"][1] == 0:
        # Skip module
        if verbose : print( "\nSKIPPED:\n" \
                            "'run_modules'[1] parameter == 0.\n" \
                            "Assuming all data is already registered/processed.\n" \
                            "Skipping registration process. " \
                            "Added expected nifti paths to 'paths'.")
        return paths, settings
    elif settings["run_modules"][1] == 1:   
        # Run module
        # TODO: Implement registration module

        if verbose : print_header("\nREGISTRATION FINISHED")
        return paths, settings

    else:
        raise ValueError(   "parameter run_modules should be a list containing only 0's and 1's. " \
                            "Please check the config file (config.json).")


if __name__ == "__main__":
    registration(*preprocessing(*initialization()))