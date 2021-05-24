"""DBSplan - CT Registration module

This module performs the CT coregistration process.
Here, we register all MRI scans and segmentation results to
the pre-operative CT image.
It may be called from the `registration_ct` function.
"""

# Path setup
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(root, "src")
if root not in sys.path: sys.path.append(root)
if src not in sys.path: sys.path.append(src)

# File-specific imports
from initialization import initialization       # noqa: E402
from preprocessing import preprocessing         # noqa: E402
from registration_mri import registration_mri   # noqa: E402
from segmentation import segmentation           # noqa: E402
from util.style import print_header             # noqa: E402
from util.general import log_dict               # noqa: E402


def registration_ct(paths: dict, settings: dict, verbose: bool = True) \
        -> tuple[dict, dict]:
    """
    This is the main wrapper function for the registration module.
    It calls on other functions to perform specific tasks.
    """

    if verbose: print_header("\n==== MODULE 4 - CT CO-REGISTRATION ====")

    # Check whether module should be run (from config file)
    if settings["runModules"][3] == 0:
        # Skip module
        if verbose: print("\nSKIPPED:\n"
                          "'run_modules'[4] parameter == 0.\n"
                          "Assuming all data is already registered.\n"
                          "Skipping registration process. "
                          "Added expected nifti paths to 'paths'.")

    elif settings["runModules"][3] == 1:
        # Run module
        # TODO: Implement registration module

        if verbose: print_header("\nREGISTRATION FINISHED")

    else:
        raise ValueError("parameter run_modules should be a list "
                         "containing only 0's and 1's. "
                         "Please check the config file (config.json).")

    # Log paths and settings
    log_dict(paths, os.path.join(paths["logsDir"], "paths.json"))
    log_dict(settings, os.path.join(paths["logsDir"], "settings.json"))

    return paths, settings


if __name__ == "__main__":
    paths, settings = \
        segmentation(*registration_mri(*preprocessing(*initialization())))
    registration_ct(paths, settings)
