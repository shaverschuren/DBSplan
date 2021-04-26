import sys
if "" not in sys.path : sys.path.append("")
if "src" not in sys.path : sys.path.append("src")

import subprocess
from initialization import initialization
from preprocessing import preprocessing
from util.style import print_header


def segmentation(paths, settings, verbose=True):
    """
    This is the main wrapper function for the segmentation module.
    It calls on other functions to perform specific tasks.
    """

    if verbose : print_header("\n==== MODULE 2 - SEGMENTATION ====")

    # Check whether module should be run (from config file)
    if settings["runModules"][1] == 0:
        # Skip module
        if verbose : print( "\nSKIPPED:\n" \
                            "'run_modules'[1] parameter == 0.\n" \
                            "Assuming all data is already segmented.\n" \
                            "Skipping segmentation process. " \
                            "Added expected nifti paths to 'paths'.")

    elif settings["runModules"][1] == 1:   
        # Run module
        # TODO: Implement segmentation module

        if verbose : print_header("\nSEGMENTATION FINISHED")

    else:
        raise ValueError(   "parameter run_modules should be a list containing only 0's and 1's. " \
                            "Please check the config file (config.json).")
    
    return paths, settings


if __name__ == "__main__":
    paths, settings = preprocessing(*initialization())
    segmentation(paths, settings)