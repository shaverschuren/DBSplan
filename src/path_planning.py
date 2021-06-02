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
import numpy as np                      # noqa: E402
from util.style import print_header     # noqa: E402
from util.general import log_dict       # noqa: E402
from util.nifti import load_nifti       # noqa: E402


def generate_planning_paths(paths: dict, settings: dict) -> tuple[dict, dict]:
    """
    This function generates the required processing paths
    for the path planning process.
    """

    # Create empty dicts
    paths["pathplanning_paths"] = {}
    planning_paths = {}

    # Create relevant directory and add to paths
    path_planning_dir = os.path.join(paths["tmpDataDir"], "path_planning")
    if not os.path.exists(path_planning_dir): os.mkdir(path_planning_dir)

    paths["pathplanningDir"] = path_planning_dir

    # Loop over subjects and assemble appropriate paths
    for subject in paths["ctreg_paths"]:
        # Assemble and create subject directory (+ raw dir)
        subject_dir = os.path.join(path_planning_dir, subject)
        if not os.path.exists(subject_dir): os.mkdir(subject_dir)

        raw_dir = os.path.join(subject_dir, "raw")
        if not os.path.exists(raw_dir): os.mkdir(raw_dir)

        # Create output paths
        distance_map_path = os.path.join(raw_dir, "distance_map.nii.gz")
        output_txt = os.path.join(subject_dir, "path.txt")

        # Assemble subject path dict
        subject_dict = {
            "dir": subject_dir,
            "raw": raw_dir,
            "CT": paths["nii_paths"][subject]["CT_PRE"],
            "T1w": paths["ctreg_paths"][subject]["T1w_coreg"],
            "T1w_gado": paths["ctreg_paths"][subject]["gado_coreg"],
            "final_mask": paths["ctreg_paths"][subject]["mask_final_coreg"],
            "ventricle_mask":
                paths["ctreg_paths"][subject]["mask_ventricles_coreg"],
            "sulcus_mask": paths["ctreg_paths"][subject]["mask_sulci_coreg"],
            "vessel_mask": paths["ctreg_paths"][subject]["mask_vessels_coreg"],
            "distance_map": distance_map_path,
            "output_path": output_txt
        }

        # Add subject dict to paths + planning paths
        planning_paths[subject] = subject_dict
        paths["pathplanning_paths"][subject] = subject_dict

    return planning_paths, paths


def run_path_planning(paths: dict, settings: dict, verbose: bool = True) \
        -> tuple[dict, dict]:
    """
    This funcion runs the actual path planning process.
    It calls upon `generate_planning_paths` to generate the
    appropriate paths to use for the planning process.
    """

    # Extract proper processing paths
    planning_paths, paths = generate_planning_paths(paths, settings)

    return paths, settings


def path_planning(paths: dict, settings: dict, verbose: bool = True)\
        -> tuple[dict, dict]:
    """
    This is the main wrapper function for the path planning module.
    It calls on other functions to perform specific tasks.
    """

    if verbose: print_header("\n==== MODULE 5 - PATH PLANNING ====")

    # Check whether module should be run (from config file)
    if settings["runModules"][2] == 0:
        # Skip module
        _, paths = generate_planning_paths(paths, settings)
        if verbose: print("\nSKIPPED:\n"
                          "'run_modules'[2] parameter == 0.\n"
                          "Assuming all data is already segmented.\n"
                          "Skipping segmentation process. "
                          "Added expected paths to 'paths'.")

    elif settings["runModules"][2] == 1:
        # Run module

        paths, settings = run_path_planning(paths, settings, verbose)

        if verbose: print_header("\nPATH PLANNING FINISHED")

    else:
        raise ValueError("parameter run_modules should be a list "
                         "containing only 0's and 1's. "
                         "Please check the config file (config.json).")

    # Log paths and settings
    log_dict(paths, os.path.join(paths["logsDir"], "paths.json"))
    log_dict(settings, os.path.join(paths["logsDir"], "settings.json"))

    return paths, settings
