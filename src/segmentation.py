# Path setup
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(root, "src")
if root not in sys.path: sys.path.append(root)
if src not in sys.path: sys.path.append(src)

# File-specific imports
from initialization import initialization               # noqa: E402
from preprocessing import preprocessing                 # noqa: E402
from seg.fsl import generate_fsl_paths, process_fsl     # noqa: E402
from seg.ventricles import seg_ventricles               # noqa: E402
from seg.sulci import seg_sulci                         # noqa: E402
from util.style import print_header                     # noqa: E402
from util.general import log_dict                       # noqa: E402


def segmentation(paths, settings, verbose=True):
    """
    This is the main wrapper function for the segmentation module.
    It calls on other functions to perform specific tasks.
    """

    if verbose: print_header("\n==== MODULE 2 - SEGMENTATION ====")

    # Check whether module should be run (from config file)
    if settings["runModules"][1] == 0:
        # Skip module
        _, paths = generate_fsl_paths(paths, settings)
        if verbose: print("\nSKIPPED:\n"
                          "'run_modules'[1] parameter == 0.\n"
                          "Assuming all data is already segmented.\n"
                          "Skipping segmentation process. "
                          "Added expected paths to 'paths'.")

    elif settings["runModules"][1] == 1:
        # Run module

        if verbose: print("\nRunning FSL BET/FAST...")
        paths, settings = process_fsl(paths, settings, verbose)
        if verbose: print("FSL BET/FAST completed!")

        if verbose: print("\nPerforming ventricle segmentation...")
        paths, settings = seg_ventricles(paths, settings, verbose)
        if verbose: print("Ventricle segmentation completed!")

        if verbose: print("\nPerforming sulcus segmentation...")
        seg_sulci(paths, settings, verbose)
        if verbose: print("Sulcus segmentation completed!")

        if verbose: print_header("\nSEGMENTATION FINISHED")

    else:
        raise ValueError("parameter run_modules should be a list "
                         "containing only 0's and 1's. "
                         "Please check the config file (config.json).")

    # Log paths and settings
    log_dict(paths, os.path.join(paths["logsDir"], "paths.json"))
    log_dict(settings, os.path.join(paths["logsDir"], "settings.json"))

    return paths, settings


if __name__ == "__main__":
    paths, settings = preprocessing(*initialization())
    segmentation(paths, settings)
