"""Segmentation-related module for basic mask utilities"""

import numpy as np
import nibabel as nib
from scipy import ndimage


def binarize_mask(pve_path: str, mask_path: str, treshold: float = 0.5):
    """
    This function binarizes pve maps.
    """

    # Load the PVE image
    pve_img = nib.load(pve_path)
    img_aff = pve_img.affine
    img_hdr = pve_img.header
    # Extract the actual data in a numpy array
    pve_map = pve_img.get_fdata()

    # Create mask data map
    mask_map = np.zeros(np.shape(pve_map))
    mask_map[pve_map < treshold] = 0
    mask_map[pve_map >= treshold] = 1

    # Store mask
    mask_img = nib.Nifti1Image(mask_map.astype(np.int16), img_aff, img_hdr)
    nib.save(mask_img, mask_path)


def find_center(img_as_np: np.ndarray, treshold: float = 1e-2):
    """
    This function finds the center coordinates
    of an image (bet) or binarized mask.
    """

    # Binarize image based on certain treshold
    bin_img = np.zeros(np.shape(img_as_np))
    bin_img[img_as_np < treshold] = 0
    bin_img[img_as_np >= treshold] = 1

    # Extract center of mass (center of mask)
    coords = ndimage.measurements.center_of_mass(bin_img)

    return coords
