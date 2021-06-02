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
from tqdm import tqdm                           # noqa: E402
from initialization import initialization       # noqa: E402
from preprocessing import preprocessing         # noqa: E402
from registration_mri import registration_mri   # noqa: E402
from segmentation import segmentation           # noqa: E402
from util.fsl import flirt_registration         # noqa: E402
from util.style import print_header             # noqa: E402
from util.general import log_dict               # noqa: E402


def setup_reg_paths(paths: dict, settings: dict) -> tuple[dict, dict]:
    """
    This function sets up the appropriate paths for the
    CT coregistration module. It gets run even if the module
    is skipped to ensure all paths are properly stored.
    """

    # Define appropriate directory
    ct_registrationDir = os.path.join(paths["tmpDataDir"], "ct_registration")
    if not os.path.isdir(ct_registrationDir): os.mkdir(ct_registrationDir)

    # Add directories to paths
    paths["ctregDir"] = ct_registrationDir
    paths["ctreg_paths"] = {}

    # Define subject-specific paths
    for subject in paths["nii_paths"]:
        # Define and make subject directory
        subjectDir = os.path.join(paths["ctregDir"], subject)
        if not os.path.isdir(subjectDir): os.mkdir(subjectDir)

        # Add paths to paths
        paths["ctreg_paths"][subject] = {}

        paths["ctreg_paths"][subject]["T1w_coreg"] = \
            os.path.join(subjectDir, "MRI_T1W_coreg.nii.gz")
        paths["ctreg_paths"][subject]["gado_coreg"] = \
            os.path.join(subjectDir, "MRI_T1W_GADO_coreg.nii.gz")
        paths["ctreg_paths"][subject]["mask_final_coreg"] = \
            os.path.join(subjectDir, "mask_final_coreg.nii.gz")
        paths["ctreg_paths"][subject]["mask_ventricles_coreg"] = \
            os.path.join(subjectDir, "mask_ventricles_coreg.nii.gz")
        paths["ctreg_paths"][subject]["mask_sulci_coreg"] = \
            os.path.join(subjectDir, "mask_sulci_coreg.nii.gz")
        paths["ctreg_paths"][subject]["mask_vessels_coreg"] = \
            os.path.join(subjectDir, "mask_vessels_coreg.nii.gz")
        paths["ctreg_paths"][subject]["entry_points_coreg"] = \
            os.path.join(subjectDir, "entry_points_coreg.nii.gz")
        paths["ctreg_paths"][subject]["omat"] = \
            os.path.join(subjectDir, "coreg.mat")

    return paths, settings


def coreg_ct(paths, settings, verbose):
    """
    This function performs the actual coregistration our MRI-based results
    with the CT scan (used for the purpose of improved geometric accuracy).
    It uses the paths defined in setup_reg_paths and the functionality defined
    in util.fsl.flirt_registration for this purpose. Please note that we're
    registering the T1w image to the CT image, after which all other images
    and masks will be coregistered using the same affine transformation matrix.
    """

    # Init skipped_img
    skipped_img = False

    # Define iterator
    if verbose:
        iterator = tqdm(paths["ctreg_paths"].items(), ascii=True,
                        bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}')
    else:
        iterator = paths["ctreg_paths"].items()

    # Loop over subjects
    for subject, regpaths in iterator:

        # Extract appropriate paths
        in_path = paths["nii_paths"][subject]["MRI_T1W"]
        ref_path = paths["nii_paths"][subject]["CT_PRE"]
        out_path = regpaths["T1w_coreg"]
        mat_path = regpaths["omat"]

        coreg_paths = [
            (paths["mrreg_paths"][subject]["gado_coreg"],
             regpaths["gado_coreg"]),
            (paths["seg_paths"][subject]["final_mask"],
             regpaths["mask_final_coreg"]),
            (paths["seg_paths"][subject]["ventricle_mask"],
             regpaths["mask_ventricles_coreg"]),
            (paths["seg_paths"][subject]["sulcus_mask"],
             regpaths["mask_sulci_coreg"]),
            (paths["seg_paths"][subject]["vessel_mask"],
             regpaths["mask_vessels_coreg"]),
            (paths["seg_paths"][subject]["entry_points"],
             regpaths["entry_points_coreg"])
        ]

        # Check output
        output_ok = all(
            os.path.exists(path) for _, path in regpaths.items()
        )

        if not output_ok:
            # Perform registration
            flirt_registration(in_path, ref_path, out_path,
                               omat_path=mat_path, dof=12)
            # Perform coregistrations
            for path_pair in coreg_paths:
                coreg_in = path_pair[0]
                coreg_out = path_pair[1]
                flirt_registration(coreg_in, ref_path, coreg_out,
                                   init_path=mat_path, apply_xfm=True,
                                   dof=None)
        else:
            if settings["resetModules"][3] == 0:
                skipped_img = True
            elif settings["resetModules"][3] == 1:
                # Remove previous output
                os.remove(out_path)
                os.remove(mat_path)

                # Perform registration
                flirt_registration(in_path, ref_path, out_path,
                                   omat_path=mat_path, dof=12)
                # Perform coregistrations
                for path_pair in coreg_paths:
                    coreg_in = path_pair[0]
                    coreg_out = path_pair[1]
                    flirt_registration(coreg_in, ref_path, coreg_out,
                                       init_path=mat_path, apply_xfm=True,
                                       dof=None)
            else:
                raise ValueError("Parameter 'resetModules' should be a list "
                                 "containing only 0's and 1's. "
                                 "Please check the config file (config.json).")

    # If some files were skipped, write message
    if verbose and skipped_img:
        print("Some scans were skipped due to the output being complete.\n"
              "If you want to rerun this entire module, please set "
              "'resetModules'[3] to 0 in the config.json file.")


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

        # Setup paths
        paths, settings = setup_reg_paths(paths, settings)

        # Print message
        if verbose: print("\nSKIPPED:\n"
                          "'run_modules'[3] parameter == 0.\n"
                          "Assuming all data is already registered.\n"
                          "Skipping registration process. "
                          "Added expected paths to 'paths'.")

    elif settings["runModules"][3] == 1:
        # Run module

        # Setup paths
        paths, settings = setup_reg_paths(paths, settings)

        # Run CT Coregistration
        coreg_ct(paths, settings, verbose)

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
