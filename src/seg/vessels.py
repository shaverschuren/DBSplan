import os
import nibabel as nib
from tqdm import tqdm
from skimage.filters import frangi
from util.nifti import load_nifti
from util.fsl import flirt_registration


def extract_vessels(seg_paths):
    """
    This function performs the actual segmentation part of the
    vessel segmentation. It uses some Frangi-filter based tricks
    to help in this process.
    """

    # Extract subject info
    subject = seg_paths["subject"]
    mask_path = seg_paths["vessel_mask"]

    # Extract relevant images
    T1w_gado, ori_aff, ori_hdr = load_nifti(seg_paths["T1-gado"])
    T1w_bet, _, _ = load_nifti(seg_paths["bet"])
    csf_mask, _, _ = load_nifti(seg_paths["csf"])

    # # Clean up T1w-gado image
    T1w_gado[T1w_bet > 1e-2] = 0   # Remove non-brain
    T1w_gado[csf_mask > 1e-2] = 0  # Remove CSF

    # Frangi filter T1w-gado image
    raw_mask = frangi(T1w_gado)

    # Save ventricle mask
    nii_mask = nib.Nifti1Image(raw_mask, ori_aff, ori_hdr)
    nib.save(nii_mask, mask_path)

    return


def seg_vessels(paths, settings, verbose=True):
    """
    This function performs the path management/administratory
    part of the vessel segmentation. It calls upon extract_vessels()
    to perform the actual segmentation.
    """

    # Initialize skipped_img variable
    skipped_img = False

    # If applicable, make segmentation paths and folder
    if "segDir" not in paths:
        paths["segDir"] = os.path.join(paths["tmpDataDir"], "segmentation")
    if "seg_paths" not in paths:
        paths["seg_paths"] = {}

    if not os.path.isdir(paths["segDir"]): os.mkdir(paths["segDir"])

    # Generate processing paths (iteratively)
    seg_paths = []

    for subject in paths["nii_paths"]:
        # Create subject dict
        subjectDir = os.path.join(paths["segDir"], subject)
        if not os.path.isdir(subjectDir): os.mkdir(subjectDir)

        if subject not in paths["seg_paths"]:
            paths["seg_paths"][subject] = {"dir": subjectDir}

        # Define needed paths (originals + FSL-processed)
        T1_path = paths["nii_paths"][subject]["MRI_T1W"]
        T1_gado_path = paths["mrreg_paths"][subject]["gado_coreg"]
        fsl_bet_path = paths["fsl_paths"][subject]["bet"]
        fsl_csf_path = paths["fsl_paths"][subject]["fast_csf"]

        # Assemble segmentation path
        vessel_mask_path = os.path.join(subjectDir, "vessel_mask.nii.gz")

        # Add paths to {paths}
        paths["seg_paths"][subject]["vessel_mask"] = vessel_mask_path

        # Add paths to seg_paths
        subject_dict = {"subject": subject,
                        "T1": T1_path,
                        "T1-gado": T1_gado_path,
                        "bet": fsl_bet_path,
                        "csf": fsl_csf_path,
                        "vessel_mask": vessel_mask_path}

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
        output_ok = os.path.exists(sub_paths["vessel_mask"])

        # Determine whether to skip subject
        if output_ok:
            if settings["resetModules"][2] == 0:
                skipped_img = True
                continue
            elif settings["resetModules"][2] == 1:
                # Generate sulcus mask
                extract_vessels(sub_paths)
            else:
                raise ValueError("Parameter 'resetModules' should be a list "
                                 "containing only 0's and 1's. "
                                 "Please check the config file (config.json).")
        else:
            # Generate sulcus mask
            extract_vessels(sub_paths)

    # If some files were skipped, write message
    if verbose and skipped_img:
        print("Some scans were skipped due to the output being complete.\n"
              "If you want to rerun this entire module, please set "
              "'resetModules'[2] to 0 in the config.json file.")

    return paths, settings
