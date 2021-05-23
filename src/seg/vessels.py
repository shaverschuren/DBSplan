import os
import itk
import warnings
import numpy as np
import nibabel as nib
from typing import Optional
from tqdm import tqdm
from scipy.ndimage import affine_transform
from util.nifti import load_nifti


def backup_result(image: itk.image, aff: np.ndarray,
                  nii_header: nib.nifti1.Nifti1Header, filename: str):
    """
    This function may be used to back-up intermediate results
    of the segmentation processing pipeline.
    """

    # Create nibabel image object
    nii_backup = nib.Nifti1Image(
        np.moveaxis(np.asarray(image), [0, 1, 2], [2, 1, 0]),
        aff, nii_header
    )

    # Save image
    nib.save(nii_backup, filename)


def anisotropic_diffusion_smoothing(image: itk.Image,
                                    timeStep: float = 0.05,
                                    nIter: int = 3,
                                    conductance: float = 5.0) -> itk.Image:
    """
    Here, we perform an anisotropic diffusion smoothing algorithm.
    Hereby, we remove noise from the image while still maintaining the edges.
    Documentation as described in:
    https://itk.org/ITKExamples/src/Filtering/AnisotropicSmoothing/ComputeCurvatureAnisotropicDiffusion/Documentation.html
    """

    # Cast image to itk.F
    image_F = image.astype(itk.F)

    # Setup image parameters
    InputPixelType = itk.F
    OutputPixelType = itk.F
    Dimension = image.GetImageDimension()

    InputImageType = itk.Image[InputPixelType, Dimension]
    OutputImageType = itk.Image[OutputPixelType, Dimension]

    # Perform filtering
    smoothed_img = itk.curvature_anisotropic_diffusion_image_filter(
        image_F, number_of_iterations=nIter, time_step=timeStep,
        conductance_parameter=conductance,
        ttype=[InputImageType, OutputImageType]
    )

    return smoothed_img


def hessian_vesselness(image: itk.Image, voxDim: float,
                       sigmaRange: list = [0.1, 1.0], nSteps: int = 10,
                       alpha: Optional[float] = 0.5,
                       beta: Optional[float] = 0.5,
                       gamma: Optional[float] = 20.0) -> itk.Image:
    """
    Here, we make use of the 3D multiscale Hessian-based
    vesselness filter by Antiga et al., as is described in:
    https://itk.org/Doxygen/html/classitk_1_1MultiScaleHessianBasedMeasureImageFilter.html
    https://itk.org/ITKExamples/src/Nonunit/Review/SegmentBloodVesselsWithMultiScaleHessianBasedMeasure/Documentation.html
    """

    # Cast image to itk.F
    image_F = image.astype(itk.F)

    # Setup image parameters
    PixelType = itk.F
    Dimension = image_F.GetImageDimension()

    ImageType = itk.Image[PixelType, Dimension]

    # Set-up parameters
    sigmaMin = sigmaRange[0] / voxDim
    sigmaMax = sigmaRange[1] / voxDim

    # Set-up Hessian image type
    HessianPixelType = itk.SymmetricSecondRankTensor[itk.D, Dimension]
    HessianImageType = itk.Image[HessianPixelType, Dimension]

    # Set-up Hessian-to-objectness filter
    objectness_filter = itk.HessianToObjectnessMeasureImageFilter[
        HessianImageType, ImageType].New()
    objectness_filter.SetBrightObject(True)
    objectness_filter.SetScaleObjectnessMeasure(False)
    if alpha: objectness_filter.SetAlpha(alpha)
    if beta: objectness_filter.SetBeta(beta)
    if gamma: objectness_filter.SetGamma(gamma)

    # Set-up the Multi-scale Hessian filter
    multi_scale_filter = itk.MultiScaleHessianBasedMeasureImageFilter[
        ImageType, HessianImageType, ImageType].New()
    multi_scale_filter.SetInput(image_F)
    multi_scale_filter.SetHessianToMeasureFilter(objectness_filter)
    multi_scale_filter.SetSigmaMinimum(sigmaMin)
    multi_scale_filter.SetSigmaMaximum(sigmaMax)
    multi_scale_filter.SetNumberOfSigmaSteps(nSteps)

    # Obtain output
    multi_scale_filter.Update()
    vesselness_img = multi_scale_filter.GetOutput()

    return vesselness_img


def vesselness_thresholding(image: itk.Image, threshold: float = 1.5,
                            nonzeros: bool = True) -> itk.Image:
    """
    This function thresholds the vesselness map.
    The threshold is set to the mean +/- a certain times (param: threshold)
    the std.
    """

    # Import vesselness image to numpy
    vesselness_as_np = itk.array_from_image(image)
    np.moveaxis(vesselness_as_np, [0, 1, 2], [2, 1, 0])

    # Determine threshold
    if nonzeros:
        mean = np.mean(vesselness_as_np[vesselness_as_np > 1e-4])
        std = np.std(vesselness_as_np[vesselness_as_np > 1e-4])
    else:
        mean = np.mean(vesselness_as_np)
        std = np.std(vesselness_as_np)

    abs_threshold = mean + threshold * std

    # Check whether threshold is appropriate
    if abs_threshold > np.max(vesselness_as_np):
        warnings.warn("The vesselness threshold is higher than "
                      "the maximal vesselness value:\n"
                      f"{abs_threshold:.2f} > {np.max(vesselness_as_np):.2f}"
                      "\nPlease adjust the threshold manually.")

    # Threshold image
    vesselness_as_np[vesselness_as_np < abs_threshold] = 0.
    vesselness_as_np[vesselness_as_np >= abs_threshold] = 1.

    # Export vesselness image back to itk
    image_out = itk.image_from_array(vesselness_as_np)

    return image_out


def fastmarching_segmentation(image: itk.Image, seed_mask: itk.Image,
                              affine_matrix: np.ndarray,
                              nii_header: nib.nifti1.Nifti1Header,
                              logsDir: str,
                              gradientMagnitudeSigma: float = 1e-2,
                              sigmoidAlpha: float = -15.0,
                              sigmoidBeta: float = 60.0,
                              timeThreshold: int = 5,
                              stoppingTime: int = 5,
                              smoothInput: bool = False,
                              useGradientMagnitudeAsSpeed: bool = False,
                              backupInterResults: bool = True) -> itk.Image:
    """
    Here, we implement the fastmarching segmentation (ITK),
    as is documented (for C++) at:
    https://itk.org/Doxygen/html/itkFastMarchingImageFilter_8h_source.html
    """

    # Determine voxel size
    avg_vox_dim = np.mean((affine_matrix.diagonal())[:-1])

    # Cast image to itk.F
    image_F = image.astype(itk.F)
    ImageType = itk.Image[itk.F, image.GetImageDimension()]

    # If applicable, apply smoothing to input
    if smoothInput:
        smoothed_image = anisotropic_diffusion_smoothing(image_F)
    else:
        smoothed_image = image_F

    # Calculate gradient magnitude image (used later as speed map)
    gradientMagnitude_image = \
        itk.gradient_magnitude_recursive_gaussian_image_filter(
            smoothed_image, sigma=gradientMagnitudeSigma / avg_vox_dim
        )

    if backupInterResults:
        backup_result(gradientMagnitude_image, affine_matrix, nii_header,
                      os.path.join(logsDir, "4_1_gradient_magnitude.nii.gz"))

    # Calculate speed map by applying sigmoid filter to gradMag-image
    # or intensity image. Work in progress...
    # TODO: Threshold gradient magnitude and use as no go-zones?
    if useGradientMagnitudeAsSpeed:
        speedMap_image = itk.sigmoid_image_filter(
            gradientMagnitude_image,
            output_minimum=0.0, output_maximum=1.0,
            alpha=sigmoidAlpha, beta=sigmoidBeta
        )
    else:
        speedMap_image = itk.sigmoid_image_filter(
            smoothed_image,
            output_minimum=0.0, output_maximum=1.0,
            alpha=67.0, beta=500
        )

    # Set speed in non-brain to 0
    speedMap_np = np.asarray(speedMap_image)
    image_np = np.asarray(image_F)

    speedMap_np[image_np < 1e-2 * np.mean(image_np)] = 0.

    speedMap_image = itk.GetImageFromArray(speedMap_np)

    if backupInterResults:
        backup_result(speedMap_image, affine_matrix, nii_header,
                      os.path.join(logsDir, "4_2_speed_map_sigmoid.nii.gz"))

    # Generate appropriate seed mask format (image to list of points)
    if backupInterResults:
        backup_result(seed_mask, affine_matrix, nii_header,
                      os.path.join(logsDir, "4_3_seed_mask.nii.gz"))

    seed_idx = np.nonzero(np.asarray(seed_mask))

    NodeType = itk.LevelSetNode.F3
    NodeContainer = itk.VectorContainer[itk.UI, NodeType]
    SeedPoints = NodeContainer.New()
    SeedPoints.Initialize()

    for i in range(np.shape(seed_idx)[1]):
        id_x = int(seed_idx[2][i])
        id_y = int(seed_idx[1][i])
        id_z = int(seed_idx[0][i])

        node = NodeType()
        node.SetIndex((id_x, id_y, id_z))
        node.SetValue(0.0)

        SeedPoints.InsertElement(i, node)

    # Perform FastMarching
    # https://www.orfeo-toolbox.org/SoftwareGuide/SoftwareGuidech16.html

    fastMarching_image = itk.fast_marching_image_filter(
        speedMap_image, trial_points=SeedPoints,
        stopping_value=stoppingTime,
        ttype=[ImageType, ImageType]
    )

    # Threshold FastMarching output
    image_out = itk.binary_threshold_image_filter(
        fastMarching_image,
        lower_threshold=0.0, upper_threshold=timeThreshold,
        outside_value=0.0, inside_value=1.0
    )

    return image_out


def levelset_segmentation(image: np.ndarray,
                          affine_matrix: np.ndarray,
                          nii_header: nib.nifti1.Nifti1Header,
                          logsDir: str) -> np.ndarray:
    """
    This function implements the *LevelSet* vessel segmentation
    method, as is described by Neumann et al., 2019
    (doi: https://doi.org/10.1016/j.cmpb.2019.105037).
    We will be implementing this method in Python via the ITK
    software package. The process consists of several steps:
    - Firstly, we apply an edge-preserving anisotropic diffusion
      filtering algorithm to the input image.
    - Then, we generate a Hessian-based vesselness map, for which
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
    img_itk = (itk.GetImageFromArray(image))
    image_in = img_itk.astype(itk.F)

    # --- Anisotropic diffusion smoothing ---

    # Apply filter
    smoothed_img = anisotropic_diffusion_smoothing(image_in)
    # Backup image
    backup_result(smoothed_img, affine_matrix, nii_header,
                  os.path.join(logsDir, "1_anisotropic_diff_smoothing.nii.gz"))

    # --- Hessian-based vesselness map ---

    # Apply filter
    vesselness_img = hessian_vesselness(smoothed_img, avg_vox_dim)
    # Backup image
    backup_result(vesselness_img, affine_matrix, nii_header,
                  os.path.join(logsDir, "2_hessian_based_vesselness.nii.gz"))

    # --- Threshold image at (mean + 1.5 * std) ---

    # Apply filter
    thresholded_img = vesselness_thresholding(vesselness_img)
    # Backup image
    backup_result(thresholded_img, affine_matrix, nii_header,
                  os.path.join(logsDir, "3_thresholded_vesselness.nii.gz"))

    # --- FastMarching segmentation ---

    # Apply filter
    fastmarching_img = fastmarching_segmentation(
        smoothed_img, thresholded_img, affine_matrix, nii_header, logsDir
    )
    # Backup image
    backup_result(fastmarching_img, affine_matrix, nii_header,
                  os.path.join(logsDir, "4_fastmarching_segmentation.nii.gz"))

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

    # Create back-up directory (for intermediate results)
    logsDir = seg_paths["backupDir"]

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
    raw_mask = levelset_segmentation(T1w_gado, ori_aff, ori_hdr, logsDir)

    # Clean up mask
    vessel_mask = raw_mask
    vessel_mask[T1w_bet < 1e-2] = 0   # Remove non-brain
    # vessel_mask[csf_mask > 1e-2] = 0  # Remove CSF

    # Save vessel mask
    nii_mask = nib.Nifti1Image(raw_mask, ori_aff, ori_hdr)
    # nib.save(nii_mask, seg_paths["vessel_mask"])


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

        # Create backup dict
        backupDir = os.path.join(subjectDir, "vessel_debug")
        if not os.path.isdir(backupDir): os.mkdir(backupDir)

        # Create subject dict in paths dict
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
                        "vessel_mask": vessel_mask_path,
                        "backupDir": backupDir}

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
