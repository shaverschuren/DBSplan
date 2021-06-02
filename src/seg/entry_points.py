import os
from tqdm import tqdm
import numpy as np
import nibabel as nib
import skimage.morphology as morph
from scipy.ndimage import affine_transform
from util.nifti import load_nifti
from util.freesurfer import extract_tissues


def find_mask_edges(mask: np.ndarray) -> np.ndarray:
    """
    This function finds the edges/borders of a mask.
    In our context, it is used to find the appropriate
    entrance points for the relatively thick ribbon mask.
    """

    # Define morphological element
    element = morph.ball(1)

    # Perform erosion
    mask_eroded = morph.binary_erosion(mask, element)

    # Generate border masks
    mask_borders = mask - mask_eroded

    return mask_borders


def extract_entry_points(processing_paths: dict,
                         threshold_sulc: float = -3.0,
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

    # Extract frontal lobe
    frontal_lobe_labels = [1003, 1027, 1028, 2003, 2027, 2028]
    extract_tissues(processing_paths["fs_labels_path"],
                    processing_paths["frontal_lobe_path"],
                    frontal_lobe_labels)

    # Import frontal lobe mask to numpy
    frontal_lobe_mask, aff_fl, _ = \
        load_nifti(processing_paths["frontal_lobe_path"])

    # Perform affine transform (if applicable)
    if not (aff_fl == aff).all():
        aff_translation = (np.linalg.inv(aff_fl)).dot(aff)
        frontal_lobe_mask = affine_transform(
            frontal_lobe_mask, aff_translation,
            output_shape=np.shape(mask)
        )

    # Remove all non-frontal lobe voxels from entry point mask
    mask[frontal_lobe_mask < 1e-2] = 0.0

    # Find edges of WM entry region
    mask = find_mask_edges(mask)

    # Import no-go mask to numpy
    nogo_mask, aff_nogo, _ = \
        load_nifti(processing_paths["nogo_mask"])

    # Perform affine transform (if applicable)
    if not (aff_nogo == aff).all():
        aff_translation = (np.linalg.inv(aff_nogo)).dot(aff)
        nogo_mask = affine_transform(
            nogo_mask, aff_translation,
            output_shape=np.shape(mask)
        )

    # Remove all no-go voxels from entry point mask
    # mask[nogo_mask < 1e-2] = 0.0 -> TODO: Keep this or not?

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
            "fs_labels_path": seg_paths["fs_labels"],
            "nogo_mask": seg_paths["final_mask"],
            "frontal_lobe_path":
                os.path.join(seg_paths["raw"], "frontal_lobe.nii.gz"),
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
