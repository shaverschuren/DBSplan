import os
import nibabel as nib
import numpy as np
import skimage.morphology as morph
from shutil import copyfile
from tqdm import tqdm
from seg.mask_util import find_center, binarize_mask
from util.nifti import load_nifti
from util.freesurfer import extract_tissues, mgz2nii


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


def fsl_seg_ventricles(paths, settings, verbose=True):
    """
    This function performs the quick and dirty variation
    of the ventricle segmentation. It doesn't make use
    of (slow) FreeSurfer output and uses some morphological tricks
    and FSL to reach the same goal. This is less robust but very fast.
    """

    # Init skipped_img
    skipped_img = False

    # Generate processing paths (iteratively)
    seg_paths = []

    for subject, fsl_paths in paths["fsl_paths"].items():
        # Create subject dict
        subjectDir = os.path.join(paths["segDir"], subject)
        if not os.path.isdir(subjectDir): os.mkdir(subjectDir)

        paths["seg_paths"][subject] = {"dir": subjectDir}

        # Extract fsl path
        t1w_cor_path = fsl_paths["fast_corr"]
        csf_pve_path = fsl_paths["fast_csf"]

        # Assemble segmentation paths
        csf_mask_path = os.path.join(subjectDir, "csf_mask.nii.gz")
        ventricle_mask_path = os.path.join(subjectDir, "ventricle_mask.nii.gz")

        # Add paths to {paths}
        paths["seg_paths"][subject]["csf_mask"] = csf_mask_path
        paths["seg_paths"][subject]["ventricle_mask"] = ventricle_mask_path

        # Add paths to seg_paths
        seg_paths.append([subject, t1w_cor_path, csf_pve_path,
                          csf_mask_path, ventricle_mask_path])

    # Now, loop over seg_paths and perform ventricle segmentation
    # Define iterator
    if verbose:
        iterator = tqdm(seg_paths, ascii=True,
                        bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}')
    else:
        iterator = seg_paths

    # Main loop
    for sub_paths in iterator:
        # Check whether output already there
        csf_mask_ok = os.path.exists(sub_paths[3])
        ven_mask_ok = os.path.exists(sub_paths[4])
        output_ok = (csf_mask_ok and ven_mask_ok)

        # Determine whether to skip subject
        if output_ok:
            if settings["resetModules"][1] == 0:
                skipped_img = True
                continue
            elif settings["resetModules"][1] == 1:
                # Binarize the pve map to a 0/1 mask
                binarize_mask(sub_paths[2], sub_paths[3], treshold=0.8)
                # Generate ventricle mask
                extract_ventricles_fsl(sub_paths[1], sub_paths[3],
                                       sub_paths[4])
            else:
                raise ValueError("Parameter 'resetModules' should be a list "
                                 "containing only 0's and 1's. "
                                 "Please check the config file (config.json).")
        else:
            # Binarize the pve map to a 0/1 mask
            binarize_mask(sub_paths[2], sub_paths[3], treshold=0.8)
            # Generate ventricle mask
            extract_ventricles_fsl(sub_paths[1], sub_paths[3], sub_paths[4])

    return paths, settings, skipped_img


def fs_seg_ventricles(paths, settings, verbose=True):
    """
    This function performs the quick and dirty variation
    of the ventricle segmentation. It doesn't make use
    of (slow) FreeSurfer output and uses some morphological tricks
    to reach the same goal. This is less robust but very fast.
    """

    # Init skipped_img
    skipped_img = False

    # Generate processing paths (iteratively)
    seg_paths = []

    for subject, fs_path in paths["fs_paths"].items():
        # Create subject dict
        subjectDir = os.path.join(paths["segDir"], subject)
        if not os.path.isdir(subjectDir): os.mkdir(subjectDir)

        paths["seg_paths"][subject] = {"dir": subjectDir}

        # Define needed FreeSurfer paths
        t1w_mgz_path = os.path.join(fs_path, "mri", "T1.mgz")
        label_mgz_path = os.path.join(fs_path, "mri", "aparc+aseg.mgz")

        # Define nifti conversion paths
        t1w_nii_path = os.path.join(fs_path, "nifti", "T1.nii.gz")
        label_nii_path = os.path.join(fs_path, "nifti", "aparc+aseg.nii.gz")

        if not os.path.isdir(os.path.join(fs_path, "nifti")):
            os.mkdir(os.path.join(fs_path, "nifti"))

        # Assemble segmentation path
        label_seg_path = os.path.join(subjectDir, "fs_aparc+aseg.nii.gz")
        ventricle_mask_path = os.path.join(subjectDir, "ventricle_mask.nii.gz")

        # Add paths to {paths}
        paths["seg_paths"][subject]["fs_labels"] = label_seg_path
        paths["seg_paths"][subject]["ventricle_mask"] = ventricle_mask_path

        # Add paths to seg_paths
        seg_paths.append([subject, t1w_mgz_path, label_mgz_path,
                          t1w_nii_path, label_nii_path, label_seg_path,
                          ventricle_mask_path])

    # Now, loop over seg_paths and perform ventricle segmentation
    # Define iterator
    if verbose:
        iterator = tqdm(seg_paths, ascii=True,
                        bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}')
    else:
        iterator = seg_paths

    # Main loop
    for sub_paths in iterator:
        # Check whether output already there
        fs_label_ok = os.path.exists(sub_paths[5])
        ven_mask_ok = os.path.exists(sub_paths[6])
        output_ok = (fs_label_ok and ven_mask_ok)

        # Determine whether to skip subject
        if output_ok:
            if settings["resetModules"][1] == 0:
                skipped_img = True
                continue
            elif settings["resetModules"][1] == 1:
                # Perform some file structure changes.
                mgz2nii(sub_paths[1], sub_paths[3])   # t1 (mgz-->nii)
                mgz2nii(sub_paths[2], sub_paths[4])   # aparc+aseg (mgz-->nii)
                copyfile(sub_paths[4], sub_paths[5])  # aparc+aseg (fs-->seg)
                # Generate ventricle mask
                extract_ventricles_fs(sub_paths[2], sub_paths[6])
            else:
                raise ValueError("Parameter 'resetModules' should be a list "
                                 "containing only 0's and 1's. "
                                 "Please check the config file (config.json).")
        else:
            # Perform some file structure changes.
            mgz2nii(sub_paths[1], sub_paths[3])       # t1 (mgz-->nii)
            mgz2nii(sub_paths[2], sub_paths[4])       # aparc+aseg (mgz-->nii)
            copyfile(sub_paths[4], sub_paths[5])      # aparc+aseg (fs-->seg)
            # Generate ventricle mask
            extract_ventricles_fs(sub_paths[2], sub_paths[6])

    return paths, settings, skipped_img


def seg_ventricles(paths, settings, verbose=True):
    """
    This function performs the ventricle segmentation.
    It has two variations, one of which is the FreeSurfer
    based implementation, which builds upon previously run
    FreeSurfer output. The other variation makes use of morphology
    and is much quicker, yet less robust.
    """

    # Initialize skipped_img variable
    skipped_img = False

    # If applicable, make segmentation paths and folder
    if "segDir" not in paths:
        paths["segDir"] = os.path.join(paths["tmpDataDir"], "segmentation")
    if "seg_paths" not in paths:
        paths["seg_paths"] = {}

    if not os.path.isdir(paths["segDir"]): os.mkdir(paths["segDir"])

    # Perform the actual ventricle extraction in one of two modes
    if settings["quick_and_dirty"] == 1:
        paths, settings, skipped_img = \
            fsl_seg_ventricles(paths, settings, verbose)
    elif settings["quick_and_dirty"] == 0:
        paths, settings, skipped_img = \
            fs_seg_ventricles(paths, settings, verbose)

    # If some files were skipped, write message
    if verbose and skipped_img:
        print("Some scans were skipped due to the output being complete.\n"
              "If you want to rerun this entire module, please set "
              "'resetModules'[1] to 0 in the config.json file.")

    return paths, settings
