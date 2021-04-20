import sys
if "" not in sys.path : sys.path.append("")
if "src" not in sys.path : sys.path.append("src")

import os
import warnings
from util.style import print_header
from util.general import extract_json


def generate_process_paths(paths, settings):
    """
    This function generates an array of strings (paths). 
    It contains all paths required for the preprocessing process.
    We'll use info from dicts 'paths' and 'settings'.
    """

    process_paths = []

    # Extract data from the usedScans.json file
    usedScans_file = os.path.join(paths["projectDir"], settings["usedScans_file"])
    dcmPaths_dict = extract_json(usedScans_file)

    # Loop over scan types (T1w, T1w-GADO and CT)
    for scanType, pathArray in dcmPaths_dict.items():
        # Loop over subjects, dcm paths
        for subject, path in pathArray.items():
            # Find paths for the actual dcm folder and to-be-created nifti-file
            if type(path) in [list, str]:
                dcm_path = os.path.join(paths["source_dcm"][subject], *path)
                nii_path = os.path.join(paths["sourcedataDir"], "nifti", subject, scanType + ".nii")

                if os.path.exists(dcm_path):
                    process_paths.append([dcm_path, nii_path])
                else:
                    raise ValueError(f"Dicom path '{dcm_path}' doesn't exist.")
            else:
                pass

    return process_paths


def dcm2nii(process_paths, verbose=True):
    # TODO: Implement dcm2nii file conversion.
    return


def preprocessing(paths, settings, verbose=True):
    """
    This function is the main function for the preprocessing step.
    It calls on other functions to perform some tasks, such as:
    - DICOM - NIFTI conversion
    - File structure management
    """

    if verbose : print_header("\n==== MODULE 1 - PREPROCESSING ====")

    # Check whether module should be run (from config file)
    if settings["run_modules"][0] == 0:
        # Skip module
        if verbose : print("Skipped module...")
    elif settings["run_modules"][0] == 1:   
        # Run module

        # Firstly, check which scans will have to be processed.
        process_paths = generate_process_paths(paths, settings)

        # Now, Perform the dcm2nii file conversion.
        dcm2nii(process_paths, verbose)

        if verbose : print_header("\nPREPROCESSING FINISHED")
        return

    else:
        raise ValueError("parameter run_modules should be a list containing only 0's and 1's. " \
                        "Please check the config file (config.json).")


if __name__ == "__main__":
    preprocessing(..., ...)