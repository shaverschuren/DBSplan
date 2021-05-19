import os
import itk
import argparse
import numpy as np
import nibabel as nib
from tqdm import tqdm
from scipy.ndimage import affine_transform
from util.nifti import load_nifti


def levelset_segmentation(image: np.ndarray,
                          affine_matrix: np.ndarray) -> np.ndarray:
    """
    This function implements the *LevelSet* vessel segmentation
    method, as is described by Neumann et al., 2019
    (doi: https://doi.org/10.1016/j.cmpb.2019.105037).
    We will be implementing this method in Python via the ITK
    software package. The process consists of several steps:
    - Firstly, we generate a Hessian-based vesselness map, for which
      we use the vesselness filters implemented in ITK.
    - As this image will contain a significant amount of false positive
      voxels, we now threshold this image at (mean + 2 std).
    - This thresholded map is now used as a collection of seed
      points for a FastMarching method, as is also implemented in ITK.
    - Now, we finally implement an active contour segmentation algorithm
      we call the LevelSet step. This step extends the segmentation map
      found with the FastMarching method to append some of the smaller details.
    """

    # Determine image scale
    avg_vox_dim = np.mean((affine_matrix.diagonal())[:-1])

    # Import image to itk
    img_itk = itk.GetImageFromArray(image)

    # --- Hessian-based vesselness map ---
    # Here, we make use of the 3D multiscale Hessian-based
    # vesselness filter by Antiga et al., as is described in:
    # https://itk.org/Doxygen/html/classitk_1_1MultiScaleHessianBasedMeasureImageFilter.html
    # https://itk.org/ITKExamples/src/Nonunit/Review/SegmentBloodVesselsWithMultiScaleHessianBasedMeasure/Documentation.html

    # Set input image
    input_img = img_itk

    # Set-up parameters
    vesselnessArgs = {}

    vesselnessArgs["sigmaMin"] = 0.05 / avg_vox_dim
    vesselnessArgs["sigmaMax"] = 0.5 / avg_vox_dim
    vesselnessArgs["numSteps"] = 10

    vesselnessArgs["alpha"] = 0.1       # 0.1
    vesselnessArgs["beta"] = 0.1        # 0.1
    vesselnessArgs["gamma"] = 0.1       # unknown

    # Set-up filters
    ImageType = type(input_img)
    Dimension = input_img.GetImageDimension()

    HessianPixelType = itk.SymmetricSecondRankTensor[itk.D, Dimension]
    HessianImageType = itk.Image[HessianPixelType, Dimension]

    objectness_filter = itk.HessianToObjectnessMeasureImageFilter[
        HessianImageType, ImageType
    ].New()
    objectness_filter.SetBrightObject(False)
    objectness_filter.SetScaleObjectnessMeasure(False)
    objectness_filter.SetAlpha(vesselnessArgs["alpha"])
    objectness_filter.SetBeta(vesselnessArgs["beta"])
    objectness_filter.SetGamma(vesselnessArgs["gamma"])

    multi_scale_filter = itk.MultiScaleHessianBasedMeasureImageFilter[
        ImageType, HessianImageType, ImageType
    ].New()
    multi_scale_filter.SetInput(input_img)
    multi_scale_filter.SetHessianToMeasureFilter(objectness_filter)
    multi_scale_filter.SetSigmaStepMethodToLogarithmic()
    multi_scale_filter.SetSigmaMinimum(vesselnessArgs["sigmaMin"])
    multi_scale_filter.SetSigmaMaximum(vesselnessArgs["sigmaMax"])
    multi_scale_filter.SetNumberOfSigmaSteps(vesselnessArgs["numSteps"])

    OutputPixelType = itk.UC
    OutputImageType = itk.Image[OutputPixelType, Dimension]

    rescale_filter = \
        itk.RescaleIntensityImageFilter[ImageType, OutputImageType].New()
    rescale_filter.SetInput(multi_scale_filter)

    # Perform actual vesselness filtering
    vesselness_img = rescale_filter.GetOutput()

    # --- Threshold image at (mean + 2 std) ---
    # We'll threshold the image at the mean + 2 * the standard deviation.
    # We use the numpy library for this purpose.

    # Import vesselness image to numpy
    vesselness_as_np = itk.GetArrayFromImage(vesselness_img)
    np.moveaxis(vesselness_as_np, [0, 1, 2], [2, 1, 0])

    # Determine threshold
    threshold = np.mean(vesselness_as_np) + 2 * np.std(vesselness_as_np)

    # Threshold image
    vesselness_as_np[vesselness_as_np < threshold] = 0.
    vesselness_as_np[vesselness_as_np >= threshold] = 1.

    # Export vesselness image back to itk
    thresholded_img = itk.GetImageFromArray(vesselness_as_np)

    # --- FastMarching segmentation ---
    # Here, we implement the FastMarching segmentation algorithm,
    # as is described in [...].

    # Export to numpy
    mask = itk.GetArrayFromImage(thresholded_img)
    mask = np.moveaxis(mask, [0, 1, 2], [2, 1, 0])

    return mask


def extract_vessels(seg_paths: dict):
    """
    This function performs the actual segmentation part of the
    vessel segmentation. It uses some Frangi-filter based tricks
    to help in this process.
    """

    # Extract relevant images
    T1w_gado, ori_aff, ori_hdr = load_nifti(seg_paths["T1-gado"])
    T1w_bet, bet_aff, _ = load_nifti(seg_paths["bet"])
    csf_mask, csf_aff, _ = load_nifti(seg_paths["csf"])

    # Transform CSF/BET masks to T1w-gado array space
    bet_translation = (np.linalg.inv(bet_aff)).dot(ori_aff)
    csf_translation = (np.linalg.inv(csf_aff)).dot(csf_aff)

    T1w_bet = affine_transform(T1w_bet, bet_translation,
                               output_shape=np.shape(T1w_gado))
    csf_mask = affine_transform(csf_mask, csf_translation,
                                output_shape=np.shape(T1w_gado))

    # Remove non-brain from T1CE (gado) image
    T1w_gado[T1w_bet < 1e-2] = 0

    # LevelSet vessel extraction
    raw_mask = levelset_segmentation(T1w_gado, ori_aff)

    # Clean up mask
    vessel_mask = raw_mask
    vessel_mask[T1w_bet < 1e-2] = 0   # Remove non-brain
    vessel_mask[csf_mask > 1e-2] = 0  # Remove CSF

    # Save vessel mask
    nii_mask = nib.Nifti1Image(raw_mask, ori_aff, ori_hdr)
    nib.save(nii_mask, seg_paths["vessel_mask"])


def seg_vessels(paths: dict, settings: dict, verbose: bool = True):
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
