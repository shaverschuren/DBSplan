import sys
if "" not in sys.path: sys.path.append("")
if "src" not in sys.path: sys.path.append("src")

import os
import warnings
from glob import glob
from util.general import check_os, extract_json, check_type, log_dict
from util.style import print_result, print_header
from util.checks import check_freesurfer, check_fsl


def check_system(settings):
    """
    This function checks the system for needed installations.
    Checks include:
    - FreeSurfer
    - [...]
    """
    # Initialize success variable
    success = True

    # Check for FreeSurfer and FSL
    try:
        check_freesurfer()
        check_fsl()
    except UserWarning as msg:
        success = False
        print_result(False)
        print(msg)

    return success


def extract_settings(config_data, os_str):
    """
    This function extracts the settings used for the pipeline
    from the config.json file.
    Output is in the form of a dictionary.
    """

    # Create settings dictionary. Add OS.
    settings = {"OS": os_str}

    # Extract settings from config data. Omit paths
    for key, value in config_data.items():
        if key not in ["projectDir", "relativePaths"]:
            settings[key] = value

    # Check for the existence of some needed vars
    # If they're not there, take the default and give a warning.
    if "runModules" not in settings:
        settings["runModules"] = [1, 1, 1, 1]
        warnings.warn(f"\nrunModules not defined. "
                      f"Using {settings['runModules']}.")

    if "usedScans" not in settings:
        settings["pickScans_UI"] = 1
        raise UserWarning("\nusedScans was not defined. Going to UI, "
                          "which still has to be implemented...")

    return settings


def check_paths(paths):
    """
    This function takes a dict of all paths and checks their validity.
    It raises warnings for non-existent paths.
    """

    # Initialize success/result to be True
    result = True

    # Loop over dictionary of paths
    for _, value in paths.items():

        # Check data type, act accordingly. str, dict and list supported.
        if type(value) == str:
            path = value
            if not os.path.exists(path):
                if result: print_result(False)
                warnings.warn(f"Extracted path '{path}' doesn't exist. "
                              "Check config.json file.")
                result = False
        elif type(value) == dict:
            for _, path in value.items():
                check_type(path, str)
                if not os.path.exists(path):
                    if result: print_result(False)
                    warnings.warn(f"Extracted path '{path}' doesn't exist. "
                                  "Check config.json file.")
                    result = False
        elif type(value) == list:
            for path in value:
                check_type(path, str)
                if not os.path.exists(path):
                    if result: print_result(False)
                    warnings.warn(f"Extracted path '{path}' doesn't exist. "
                                  "Check config.json file.")
                    result = False
        else:
            if result: print_result(False)
            raise ValueError(f"Unexpected value type ({type(value)}) in path "
                             "dict. Expected str, dict, list.")

    return result


def setup_paths(config_data):
    """
    This function takes in the config data from the config.json file and
    spits out all relevant paths for the pipeline as a struct.
    This includes extraction of all subject dicom paths,
    apart from those mentioned in config_data["excluded_subjects"].
    """

    # Extract the project directory
    paths = {"projectDir": config_data["projectDir"]}

    # Extract the subdirs used for the pipeline
    for folder in config_data["relativePaths"]:
        relative_path = config_data["relativePaths"][folder]
        abs_path = os.path.join(paths["projectDir"], relative_path)

        paths[folder + "Dir"] = abs_path

    # Extract source data paths (DICOM)
    paths["source_dcm"] = {}
    subject_paths = glob(os.path.join(paths["sourcedataDir"],
                                      "dicom", "SEEGBCI-*"))
    subject_names = [os.path.split(path)[-1] for path in subject_paths]

    for subject_i in range(len(subject_names)):
        if subject_names[subject_i] not in config_data["excludedSubjects"]:
            subject_path = subject_paths[subject_i]
            paths["source_dcm"][subject_names[subject_i]] = subject_path
        else:
            pass

    correct_bool = check_paths(paths)

    return paths, correct_bool


def initialization(config_path="config.json", verbose=True):
    """
    This function is the main initialization function for the DBSplan pipeline.
    It takes the path of the config file as a parameter.
    """

    if verbose: print_header("\n==== MODULE 0 - INITIALIZATION ====\n")

    # Determine OS
    if verbose: print("Determining OS...\t\t", end="", flush=True)
    os_str = check_os()
    if verbose: print_result()

    # Extract config data
    if verbose: print("Extracting config data...\t", end="", flush=True)
    config_data = extract_json(config_path)
    if verbose: print_result()

    # Setup settings
    if verbose: print("Creating settings dict...\t", end="", flush=True)
    settings = extract_settings(config_data, os_str)
    if verbose: print_result()

    # Setup paths
    if verbose: print("Setting up paths...\t\t", end="", flush=True)
    paths, success_paths = setup_paths(config_data)
    if verbose and success_paths: print_result(success_paths)

    # Check for all required installations
    if verbose: print("Checking system...\t\t", end="", flush=True)
    success_sys = check_system(settings)
    if verbose and success_sys: print_result(success_sys)

    # Check whether there were any failed checks
    if not (success_paths and success_sys):
        path_check = ("" if success_paths else "Path check\t"
                                               "(check config.json file)\n")
        sys_check = ("" if success_sys else "System check\t"
                                            "(check for requirements)\n")

        raise UserWarning("The initialization was not successful.\n"
                          "Please check the warning messages above.\n"
                          "Issues were found in:\n" + path_check + sys_check)

    # Log paths and settings
    log_dict(paths, os.path.join(paths["logsDir"], "paths.json"))
    log_dict(settings, os.path.join(paths["logsDir"], "settings.json"))

    if verbose: print_header("\nINITIALIZATION FINISHED")

    return paths, settings


if __name__ == "__main__":
    initialization()
