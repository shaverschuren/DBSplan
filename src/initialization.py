import sys
if "" not in sys.path : sys.path.append("")
if "src" not in sys.path : sys.path.append("src")

import os
import sys
from glob import glob
from util.general import check_os, extract_json, print_result


def setup_paths(config_data):
    """
    This function takes in the config data from the config.json file and spits out all relevant
    paths for the pipeline as a struct. This includes extraction of all subject dicom paths, 
    apart from those mentioned in config_data["excluded_subjects"].
    """

    # Extract the project directory
    paths = {"projectDir": config_data["projectDir"]}

    # Extract the subdirs used for the pipeline
    for folder in config_data["relative_paths"]:
        relative_path = config_data["relative_paths"][folder]
        abs_path = os.path.join(paths["projectDir"], relative_path)

        paths[folder+"Dir"] = abs_path

    # Extract source data paths (DICOM)
    paths["source_dcm"] = {}
    subject_paths = glob(os.path.join(paths["sourcedataDir"], "dicom", "SEEGBCI-*"))
    subject_names = [os.path.split(path)[-1] for path in subject_paths]

    for subject_i in range(len(subject_names)):
        if subject_names[subject_i] not in config_data["excluded_subjects"]:
            paths["source_dcm"][subject_names[subject_i]] = subject_paths[subject_i]
        else:
            pass

    
    return paths


def initialize(config_path="config.json", verbose=True):
    """
    This function is the main initialization function for the DBSplan pipeline.
    It takes the path of the config file as a parameter.
    """

    if verbose : print("\n==== 01 - INITIALIZATION ====\n")

    # Determine OS
    if verbose : print("Extracting OS... ", end = "", flush=True)
    os_str = check_os()
    if verbose : print_result(True)
    
    # Extract config data
    if verbose : print("Extracting config data... ", end="", flush=True)
    config_data = extract_json(config_path)
    if verbose : print_result(True)

    # Setup paths
    if verbose : print("Setting up paths... ", end="", flush=True)
    paths = setup_paths(config_data)
    if verbose : print_result(True)

    if verbose : print("\nINITIALIZATION FINISHED")

    return paths


if __name__ == "__main__":
    initialize()