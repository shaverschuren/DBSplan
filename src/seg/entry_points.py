import os
from tqdm import tqdm
import numpy as np
import nibabel as nib
from util.nifti import load_nifti


def extract_entry_points(processing_paths: dict,
                         threshold_sulc: float = 3.0,
                         threshold_curv: float = -0.5):
    """
    This function runs the mask manipulation of the entry
    point segmentation.
    """

    # Extract sulc and curv volumes
    sulc_np, aff, hdr = load_nifti(processing_paths["sulc_path"])
    curv_np, _, _ = load_nifti(processing_paths["curv_path"])

    # Generate empty mask
    if np.shape(sulc_np) == np.shape(curv_np):
        mask = np.zeros(np.shape(sulc_np))
    else:
        raise ValueError("Arrays 'sulc' and 'curv' are not the same size!"
                         f"\nGot {np.shape(sulc_np)} and {np.shape(curv_np)}")

    # Fill mask with appropriate voxels
    for surf, threshold in [
        (sulc_np, threshold_sulc), (curv_np, threshold_curv)
    ]:
        abs_threshold = np.mean(surf) + threshold * np.std(surf)

        mask[surf < abs_threshold] = 1.0
        mask[surf == 0.0] = 0.0

    # TODO: Implement deletion of all non-frontal lobe voxels

    # Save mask
    mask_nii = nib.Nifti1Image(mask, aff, hdr)
    nib.save(mask_nii, processing_paths["output_path"])


def seg_entry_points(paths: dict, settings: dict, verbose: bool = True) \
        -> tuple[dict, dict]:
    """
    This function performs the entry point segmentation.
    It builds upon output from FreeSurfer.
    """

    # Initialize skipped_img variable
    skipped_img = False

    # If applicable, make segmentation paths and folder
    if "segDir" not in paths:
        paths["segDir"] = os.path.join(paths["tmpDataDir"], "segmentation")
    if "seg_paths" not in paths:
        paths["seg_paths"] = {}

    if not os.path.isdir(paths["segDir"]): os.mkdir(paths["segDir"])

    # Define iterator
    if verbose:
        iterator = tqdm(paths["seg_paths"].items(), ascii=True,
                        bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}')
    else:
        iterator = paths["seg_paths"].items()

    # Main subject loop
    for subject, seg_paths in iterator:
        # Determine required paths
        subject_paths = {
            "sulc_path": seg_paths["sulc_vol"],
            "curv_path": seg_paths["curv_vol"],
            "output_path":
                os.path.join(seg_paths["dir"], "entry_points.nii.gz")
        }

        # Add output path to {paths}
        paths["seg_paths"][subject]["entry_points"] = \
            subject_paths["output_path"]

        # Check whether output already there
        output_ok = os.path.exists(subject_paths["output_path"])

        if output_ok:
            if settings["resetModules"][2] == 0:
                skipped_img = True
                continue
            elif settings["resetModules"][2] == 1:
                # Extract entry points
                extract_entry_points(subject_paths)
            else:
                raise ValueError("Parameter 'resetModules' should be a list "
                                 "containing only 0's and 1's. "
                                 "Please check the config file (config.json).")
        else:
            # Extract entry points
            extract_entry_points(subject_paths)

    # If some files were skipped, write message
    if verbose and skipped_img:
        print("Some scans were skipped due to the output being complete.\n"
              "If you want to rerun this entire module, please set "
              "'resetModules'[2] to 0 in the config.json file.")

    return paths, settings
