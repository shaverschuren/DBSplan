import os
import nibabel as nib
import numpy as np
import skimage.morphology as morph
from shutil import copyfile
from tqdm import tqdm
from seg.mask_util import find_center, binarize_mask
from util.nifti import load_nifti
from util.freesurfer import extract_tissues, mgz2nii


def extract_sulci_fsl(bet_img_path, csf_mask_path, sulci_mask_path):
    """
    This function extracts the sulci from a CSF mask.
    [...]
    TODO: Implement this ...
    """

    return


def extract_sulci_fs():
    """
    This function extracts the sulci from FreeSurfer output
    [...]
    TODO: Implement this ...
    """

    return


def fsl_seg_sulci(paths, settings, verbose=True):
    """
    This function performs the quick and dirty variation
    of the sulcus segmentation. It doesn't make use
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
        sulcus_mask_path = os.path.join(subjectDir, "sulcus_mask.nii.gz")

        # Add paths to {paths}
        paths["seg_paths"][subject]["csf_mask"] = csf_mask_path
        paths["seg_paths"][subject]["sulcus_mask"] = sulcus_mask_path

        # Add paths to seg_paths
        seg_paths.append([subject, t1w_cor_path, csf_pve_path,
                          csf_mask_path, sulcus_mask_path])

    # Now, loop over seg_paths and perform sulcus segmentation
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
        sul_mask_ok = os.path.exists(sub_paths[4])
        output_ok = (csf_mask_ok and sul_mask_ok)

        # Determine whether to skip subject
        if output_ok:
            if settings["resetModules"][1] == 0:
                skipped_img = True
                continue
            elif settings["resetModules"][1] == 1:
                # Generate sulcus mask
                extract_sulci_fsl(sub_paths[1], sub_paths[3], sub_paths[4])
            else:
                raise ValueError("Parameter 'resetModules' should be a list "
                                 "containing only 0's and 1's. "
                                 "Please check the config file (config.json).")
        else:
            # Generate sulcus mask
            extract_sulci_fsl(sub_paths[1], sub_paths[3], sub_paths[4])

    return paths, settings, skipped_img


def fs_seg_sulci(paths, settings, verbose=True):
    """
    This function performs the quick and dirty variation
    of the sulcus segmentation. It doesn't make use
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
                extract_sulci_fs()
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
            extract_sulci_fs()

    return paths, settings, skipped_img


def seg_sulci(paths, settings, verbose=True):
    """
    This function performs the sulcus segmentation.
    It builds upon output from FSL BET and FAST.
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
            fsl_seg_sulci(paths, settings, verbose)
    elif settings["quick_and_dirty"] == 0:
        paths, settings, skipped_img = \
            fs_seg_sulci(paths, settings, verbose)

    # If some files were skipped, write message
    if verbose and skipped_img:
        print("Some scans were skipped due to the output being complete.\n"
              "If you want to rerun this entire module, please set "
              "'resetModules'[1] to 0 in the config.json file.")

    return paths, settings
