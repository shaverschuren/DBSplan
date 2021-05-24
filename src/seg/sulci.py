"""Sulcus segmentation"""

import os
import subprocess
import nibabel as nib
import numpy as np
import skimage.morphology as morph
from scipy.ndimage import affine_transform
from tqdm import tqdm
from util.nifti import load_nifti


def extract_sulci_fsl(bet_img_path: str, csf_mask_path: str,
                      sulci_mask_path: str):
    """
    This function extracts the sulci from a CSF mask.
    [...]
    TODO: Implement this ...
    """
    raise UserWarning("This function is not yet implemented.")


def extract_sulci_fs(seg_paths: dict):
    """
    This function extracts the sulci from FreeSurfer output.
    """

    # --- Extract appropriate paths for sulc and curv ---
    sulc = {"nii": seg_paths["sulcus_mask"].replace("sulcus_mask", "sulc_vol"),
            "ribbon": seg_paths["ribbon"],
            "rh_surf": seg_paths["rh_sulc"],
            "lh_surf": seg_paths["lh_sulc"],
            "threshold": -3.0}
    curv = {"nii": seg_paths["sulcus_mask"].replace("sulcus_mask", "curv_vol"),
            "ribbon": seg_paths["ribbon"],
            "rh_surf": seg_paths["rh_curv"],
            "lh_surf": seg_paths["lh_curv"],
            "threshold": 0.2}

    # --- Initialize main mask ---
    data, aff, hdr = load_nifti(seg_paths["ribbon"])
    mask_as_np = np.zeros(np.shape(data))

    for surf in [sulc, curv]:

        # --- Project pial surfaces to volume file ---

        # Assemble command
        command = ["mri_surf2vol",
                   "--o", surf["nii"],
                   "--ribbon", surf["ribbon"],
                   "--so", seg_paths["rh_pial"], surf["rh_surf"],
                   "--so", seg_paths["lh_pial"], surf["lh_surf"]]

        # Open stream and pass command
        recon_stream = subprocess.Popen(command, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        # Read output
        msg, error = recon_stream.communicate()
        # End stream
        recon_stream.terminate()

        if error:
            raise UserWarning("Fatal error occured during command-line "
                              "FreeSurfer usage."
                              "\nExited with error message:\n"
                              f"{error.decode('utf-8')}")

        # --- Binarize masks ---

        # Load nifti file
        data, _, _ = load_nifti(surf["nii"])

        # Calculate treshold
        treshold = np.mean(data) + surf["threshold"] * np.std(data)

        # Update mask
        mask_as_np[data > treshold] = 1
        mask_as_np[data == 0] = 0

    # --- Perform morphological closing

    # Find proper element size
    avg_vox_dim = np.mean((np.array(aff).diagonal())[:-1])
    close_element = morph.ball(int(1 / avg_vox_dim))  # Element radius +- 1 mm

    # Perform closing
    mask_as_np = morph.closing(mask_as_np, close_element)

    # --- Perform dilation (but only CSF) ---

    # Load FSL FAST-generated CSF mask
    csf_mask, aff_csf, _ = load_nifti(seg_paths["csf"])

    # Translate CSF mask to FreeSurfer arrays
    aff_translation = (np.linalg.inv(aff_csf)).dot(aff)
    csf_mask = affine_transform(csf_mask, aff_translation,
                                output_shape=np.shape(data))

    # Rebinarize csf_mask
    csf_mask[csf_mask < 0.5 * np.max(csf_mask)] = 0
    csf_mask[csf_mask >= 0.5 * np.max(csf_mask)] = 1

    # Perform dilation
    dil_element = morph.ball(int(2 / avg_vox_dim))  # Element radius +- 2 mm
    dilated_mask = morph.dilation(mask_as_np, dil_element)

    # Delete non-CSF dilation
    dilated_mask[csf_mask == 0] = 0

    # Append original mask with dilated mask
    mask_as_np[dilated_mask == 1] = 1

    # Remove ventricles
    ventricle_mask, aff_ven, _ = load_nifti(seg_paths["ventricles"])
    aff_translation = (np.linalg.inv(aff_ven)).dot(aff)
    ventricle_mask = affine_transform(ventricle_mask, aff_translation,
                                      output_shape=np.shape(data))

    mask_as_np[ventricle_mask > 0.5] = 0

    # --- Perform final (small) closing ---

    mask_as_np = morph.closing(mask_as_np, close_element)

    # --- Save mask img ---

    mask_img = nib.Nifti1Image(mask_as_np, aff, hdr)
    nib.save(mask_img, seg_paths["sulcus_mask"])


def fsl_seg_sulci(paths: dict, settings: dict, verbose: bool = True) \
        -> tuple[dict, dict, bool]:
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
            if settings["resetModules"][2] == 0:
                skipped_img = True
                continue
            elif settings["resetModules"][2] == 1:
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


def fs_seg_sulci(paths: dict, settings: dict, verbose: bool = True) \
        -> tuple[dict, dict, bool]:
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

        if subject not in paths["seg_paths"]:
            paths["seg_paths"][subject] = {"dir": subjectDir}

        # Define needed FreeSurfer paths
        T1_path = os.path.join(fs_path, "nifti", "T1.nii.gz")
        ribbon_path = os.path.join(fs_path, "mri", "ribbon.mgz")
        rh_pial_path = os.path.join(fs_path, "surf", "rh.pial.T1")
        lh_pial_path = os.path.join(fs_path, "surf", "lh.pial.T1")
        lh_curv_path = os.path.join(fs_path, "surf", "lh.curv")
        rh_curv_path = os.path.join(fs_path, "surf", "rh.curv")
        lh_sulc_path = os.path.join(fs_path, "surf", "lh.sulc")
        rh_sulc_path = os.path.join(fs_path, "surf", "rh.sulc")

        fsl_csf_path = os.path.join(paths["fsl_paths"][subject]["fast_csf"])
        csf_coreg_path = os.path.join(subjectDir, "fast_csf_coreg.nii.gz")

        ventricle_mask_path = paths["seg_paths"][subject]["ventricle_mask"]

        # Assemble segmentation path
        sulcus_mask_path = os.path.join(subjectDir, "sulcus_mask.nii.gz")

        # Add paths to {paths}
        paths["seg_paths"][subject]["sulcus_mask"] = sulcus_mask_path

        # Add paths to seg_paths
        subject_dict = {"subject": subject,
                        "T1": T1_path,
                        "ribbon": ribbon_path,
                        "rh_pial": rh_pial_path,
                        "lh_pial": lh_pial_path,
                        "rh_curv": rh_curv_path,
                        "lh_curv": lh_curv_path,
                        "rh_sulc": rh_sulc_path,
                        "lh_sulc": lh_sulc_path,
                        "csf": fsl_csf_path,
                        "csf_coreg": csf_coreg_path,
                        "ventricles": ventricle_mask_path,
                        "sulcus_mask": sulcus_mask_path}

        seg_paths.append(subject_dict)

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
        output_ok = os.path.exists(sub_paths["sulcus_mask"])

        # Determine whether to skip subject
        if output_ok:
            if settings["resetModules"][2] == 0:
                skipped_img = True
                continue
            elif settings["resetModules"][2] == 1:
                # Generate sulcus mask
                extract_sulci_fs(sub_paths)
            else:
                raise ValueError("Parameter 'resetModules' should be a list "
                                 "containing only 0's and 1's. "
                                 "Please check the config file (config.json).")
        else:
            # Generate sulcus mask
            extract_sulci_fs(sub_paths)

    return paths, settings, skipped_img


def seg_sulci(paths: dict, settings: dict, verbose: bool = True) \
        -> tuple[dict, dict]:
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
              "'resetModules'[2] to 0 in the config.json file.")

    return paths, settings
