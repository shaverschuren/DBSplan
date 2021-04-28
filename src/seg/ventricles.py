import nibabel as nib
import numpy as np
from seg.mask_util import find_center
from util.nifti import load_nifti


def extract_ventricles(bet_img_path, csf_mask_path, ventricles_mask_path):
    """
    This function extracts the ventricles from a CSF mask.
    It uses some morphological tricks for this purpose.
    """

    # Extract bet image
    bet_arr, img_aff, img_hdr = load_nifti(bet_img_path)

    # Find the center of the brain
    center_coords = find_center(bet_arr)

    # TODO: Do the actual ventricle extraction ....

    return