"""DBSplan - MRI Registration module

This module performs the MRI coregistration process.
It may be called from the `registration_mri` function.
"""

# Path setup
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(root, "src")
if root not in sys.path: sys.path.append(root)
if src not in sys.path: sys.path.append(src)

# File-specific imports
from tqdm import tqdm                       # noqa: E402
from util.fsl import flirt_registration     # noqa: E402
from util.style import print_header         # noqa: E402
from util.general import log_dict           # noqa: E402


def setup_reg_paths(paths: dict, settings: dict) -> tuple[dict, dict]:
    """
    This function sets up the appropriate paths for the
    MRI coregistration module. It gets run even if the module
    is skipped to ensure all paths are properly stored.
    """

    # Define appropriate directory
    mr_registrationDir = os.path.join(paths["tmpDataDir"], "mri_registration")
    if not os.path.isdir(mr_registrationDir): os.mkdir(mr_registrationDir)

    # Add directories to paths
    paths["mrregDir"] = mr_registrationDir
    paths["mrreg_paths"] = {}

    # Define subject-specific paths
    for subject in paths["nii_paths"]:
        # Define and make subject directory
        subjectDir = os.path.join(paths["mrregDir"], subject)
        if not os.path.isdir(subjectDir): os.mkdir(subjectDir)

        # Add paths to paths
        paths["mrreg_paths"][subject] = {}

        paths["mrreg_paths"][subject]["gado_in"] = \
            paths["nii_paths"][subject]["MRI_T1W_GADO"]
        paths["mrreg_paths"][subject]["gado_coreg"] = \
            os.path.join(subjectDir, "MRI_T1W_GADO_coreg.nii.gz")
        paths["mrreg_paths"][subject]["gado_omat"] = \
            os.path.join(subjectDir, "MRI_T1W_GADO_coreg.mat")

        # T2w (optional)
        if "MRI_T2W" in paths["nii_paths"][subject]:
            paths["mrreg_paths"][subject]["t2w_in"] = \
                paths["nii_paths"][subject]["MRI_T2W"]
            paths["mrreg_paths"][subject]["t2w_coreg"] = \
                os.path.join(subjectDir, "MRI_T2W_coreg.nii.gz")
            paths["mrreg_paths"][subject]["t2w_omat"] = \
                os.path.join(subjectDir, "MRI_T2W_coreg.mat")
        # IR (optional)
        if "MRI_IR" in paths["nii_paths"][subject]:
            paths["mrreg_paths"][subject]["ir_in"] = \
                paths["nii_paths"][subject]["MRI_IR"]
            paths["mrreg_paths"][subject]["ir_coreg"] = \
                os.path.join(subjectDir, "MRI_IR_coreg.nii.gz")
            paths["mrreg_paths"][subject]["ir_omat"] = \
                os.path.join(subjectDir, "MRI_IR_coreg.mat")
        # FLAIR (optional)
        if "MRI_FLAIR" in paths["nii_paths"][subject]:
            paths["mrreg_paths"][subject]["flair_in"] = \
                paths["nii_paths"][subject]["MRI_FLAIR"]
            paths["mrreg_paths"][subject]["flair_coreg"] = \
                os.path.join(subjectDir, "MRI_FLAIR_coreg.nii.gz")
            paths["mrreg_paths"][subject]["flair_omat"] = \
                os.path.join(subjectDir, "MRI_FLAIR_coreg.mat")

    return paths, settings


def coreg_mri(paths: dict, settings: dict, verbose: bool = True):
    """
    This function performs the actual coregistration of
    the MRI scans. It uses the paths defined in setup_reg_paths
    and the functionality defined in util.fsl.flirt_registration for
    this purpose. Please note that we're registering the GADO T1w image
    to the non-GADO T1w image.
    """

    # Init skipped_img
    skipped_img = False

    # Define iterator
    if verbose:
        iterator = tqdm(paths["mrreg_paths"].items(), ascii=True,
                        bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}')
    else:
        iterator = paths["mrreg_paths"].items()

    # Loop over subjects
    for subject, regpaths in iterator:

        # Extract appropriate reference path
        ref_path = paths["nii_paths"][subject]["MRI_T1W"]

        # Loop over other MRI scans and register to T1w
        for scan_name, in_path in regpaths.items():
            # Check whether file is indeed to be registered
            if "_coreg" not in scan_name:
                continue

            # Extract proper filenames
            in_path = regpaths[scan_name.replace("_coreg", "_in")]
            out_path = regpaths[scan_name]
            mat_path = regpaths[scan_name.replace("_coreg", "_omat")]

            # Check output
            output_ok = (os.path.exists(out_path) and os.path.exists(mat_path))

            if not output_ok:
                # Perform registration
                flirt_registration(
                    in_path, ref_path, out_path,
                    omat_path=mat_path, dof=12)
            else:
                if settings["resetModules"][2] == 0:
                    skipped_img = True
                elif settings["resetModules"][2] == 1:
                    # Remove previous output
                    os.remove(out_path)
                    os.remove(mat_path)

                    # Perform registration
                    flirt_registration(
                        in_path, ref_path, out_path,
                        omat_path=mat_path, dof=12)
                else:
                    raise ValueError(
                        "Parameter 'resetModules' should be a list "
                        "containing only 0's and 1's. "
                        "Please check the config file (config.json)."
                    )

    # If some files were skipped, write message
    if verbose and skipped_img:
        print("Some scans were skipped due to the output being complete.\n"
              "If you want to rerun this entire module, please set "
              "'resetModules'[1] to 0 in the config.json file.")


def registration_mri(paths: dict, settings: dict, verbose: bool = True) \
        -> tuple[dict, dict]:
    """
    This is the main wrapper function for the mri registration module.
    It calls on other functions to perform specific tasks.
    """

    if verbose: print_header("\n==== MODULE 2 - MRI CO-REGISTRATION ====\n")

    # Check whether module should be run (from config file)
    if settings["runModules"][1] == 0:
        # Skip module

        # Setup paths
        paths, settings = setup_reg_paths(paths, settings)

        # Print message
        if verbose: print("\nSKIPPED:\n"
                          "'run_modules'[1] parameter == 0.\n"
                          "Assuming all data is already registered.\n"
                          "Skipping registration process. "
                          "Added expected paths to 'paths'.")

    elif settings["runModules"][1] == 1:
        # Run module

        # Setup paths
        paths, settings = setup_reg_paths(paths, settings)

        # Run MRI Coregistration
        coreg_mri(paths, settings, verbose)

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
    # Import previous module(s)
    from initialization import initialization   # noqa: E402
    from preprocessing import preprocessing     # noqa: E402
    # Run previous modules
    paths, settings = preprocessing(*initialization())
    # Run this module
    registration_mri(paths, settings)
