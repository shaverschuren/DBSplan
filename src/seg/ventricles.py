import nibabel as nib
import numpy as np
import skimage.morphology as morph
from seg.mask_util import find_center
from util.nifti import load_nifti
from util.freesurfer import extract_tissues


def find_seed_mask(csf_mask, img_aff, center_coords):
    """
    This function finds seed points for the ventricles.
    These may later be used for the region growing algorithm.
    """

    # Initialize seed_mask
    seed_mask = csf_mask

    # Determine avg voxel dimension
    avg_vox_dim = np.mean((np.array(img_aff).diagonal())[:-1])

    # Perform erosion with a ball element (radius approx 4mm)
    element = morph.ball(int(4 / avg_vox_dim))
    seed_mask = morph.erosion(seed_mask, element)

    # Find mask for "near the brain's center"
    xx, yy, zz = np.meshgrid(np.arange(np.shape(seed_mask)[0]),
                             np.arange(np.shape(seed_mask)[1]),
                             np.arange(np.shape(seed_mask)[2]),
                             indexing="ij")

    xx_offset = xx - center_coords[0]
    yy_offset = yy - center_coords[1]
    zz_offset = zz - center_coords[2]
    dist2center = np.sqrt(xx_offset ** 2 + yy_offset ** 2 + zz_offset ** 2)

    center_mask = np.zeros(np.shape(seed_mask))
    center_mask[dist2center < 20 / avg_vox_dim] = 1  # <20mm from the center

    # Remove seed points that are too far from the center
    seed_mask = seed_mask * center_mask

    return seed_mask


def region_growing(seed_mask, full_mask, img_aff, element_size=2):
    """
    This function performs a region growing algorithm.
    It makes use of a seed mask and a full mask.
    - The seed masks contains several voxels in the ROI (e.g. ventricles).
    - The full mask contains all voxels of the tissue of interest (e.g. CSF).
    - The img_aff parameter contains the affine transformation to real space.
    - The element_size parameter is the element size (radius) in [mm].
    """

    # Determine avg voxel dimension
    avg_vox_dim = np.mean((np.array(img_aff).diagonal())[:-1])

    # Build morphological structuring element
    element = morph.ball(int(element_size / avg_vox_dim))
    big_element = morph.ball(int(element_size * 1.5 / avg_vox_dim))
    small_element = morph.ball(1)

    # Perform openings of full mask
    crude_mask = full_mask
    crude_mask = morph.opening(crude_mask, big_element)
    full_mask = morph.opening(full_mask, element)

    # Perform crude region growing loop
    stop_loop = False
    previous_output = seed_mask
    new_output = seed_mask
    loop_n = 0
    while not stop_loop:
        # Update input and loop count
        loop_n += 1
        new_input = previous_output

        # Perform region growing
        new_output = morph.dilation(new_input, element)
        new_output = new_output * crude_mask

        # Check whether loop should stop
        stop_loop = (previous_output == new_output).all() or (loop_n > 50)

        # Update output var
        previous_output = new_output

    # Perform fine region growing loop
    stop_loop = False
    loop_n = 0
    while not stop_loop:
        new_input = previous_output

        # Perform region growing
        new_output = morph.dilation(new_input, small_element)
        new_output = new_output * full_mask

        # Check whether loop should stop
        stop_loop = (previous_output == new_output).all() or (loop_n > 5)

        # Update output var
        previous_output = new_output

    # Store and return final result
    processed_mask = new_output

    return processed_mask


def extract_ventricles_fsl(bet_img_path, csf_mask_path, ventricles_mask_path):
    """
    This function extracts the ventricles from a CSF mask.
    It uses some morphological tricks for this purpose.
    """

    # Extract image, csf mask
    bet_img, img_aff, img_hdr = load_nifti(bet_img_path)
    csf_mask, _, _ = load_nifti(csf_mask_path)

    # Find the center of the brain
    center_coords = find_center(bet_img)

    # Find seed mask for ventricles
    seed_mask = find_seed_mask(csf_mask, img_aff, center_coords)

    # Perform region growing
    ventricle_mask = region_growing(seed_mask, csf_mask, img_aff)

    # Save ventricle mask
    nii_mask = nib.Nifti1Image(ventricle_mask, img_aff, img_hdr)
    nib.save(nii_mask, ventricles_mask_path)


def extract_ventricles_fs(aparc_aseg_path, ventricles_mask_path):
    """
    This function extracts the ventricles from FreeSurfer output.
    We simply extract the appropriate label and perform some
    file format conversions for this purpose.
    aparc_aseg_path      --> path to aparc+aseg.mgz file
    ventricles_mask_path --> path to to-be-created ventricles .nii mask.
    """

    ventricle_labels = [4, 43]

    extract_tissues(aparc_aseg_path, ventricles_mask_path, ventricle_labels)
