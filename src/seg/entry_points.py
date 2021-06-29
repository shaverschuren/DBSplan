import os
from tqdm import tqdm
import gzip
import numpy as np
import nibabel as nib
import skimage.morphology as morph
from scipy.ndimage import affine_transform
from path_planning import generate_distance_map
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
                         threshold_sulc: float = -1.0,
                         threshold_curv: float = 0.0):
    """
    This function runs the mask manipulation of the entry
    point segmentation.
    """

    # Extract nogo-volume and, fs labels and ribbon .mgz
    # file header for spatial info
    nogo_np, aff, hdr = load_nifti(processing_paths["nogo_mask"])
    labels_np, aff_fs, _ = load_nifti(processing_paths["fs_labels_path"])

    with gzip.open(processing_paths["orig_path"], 'rb') as mgh_file_handle:
        mgh_header = \
            nib.freesurfer.mghformat.MGHHeader.from_fileobj(mgh_file_handle)

    # Generate empty mask
    mask = np.zeros(np.shape(labels_np))

    # Extract list of vertices on the pial surface
    rh_pial_points, _ = \
        nib.freesurfer.read_geometry(processing_paths["rh_pial_path"])
    lh_pial_points, _ = \
        nib.freesurfer.read_geometry(processing_paths["lh_pial_path"])
    # Extract curv and sulc values for these vertices
    rh_curv_points = \
        nib.freesurfer.read_morph_data(processing_paths["rh_curv_path"])
    lh_curv_points = \
        nib.freesurfer.read_morph_data(processing_paths["lh_curv_path"])
    rh_sulc_points = \
        nib.freesurfer.read_morph_data(processing_paths["rh_sulc_path"])
    lh_sulc_points = \
        nib.freesurfer.read_morph_data(processing_paths["lh_sulc_path"])
    # Extract annotations for these vertices
    rh_annot_points, _, labels = \
        nib.freesurfer.read_annot(processing_paths["rh_annot_path"])
    lh_annot_points, _, _ = \
        nib.freesurfer.read_annot(processing_paths["lh_annot_path"])

    # Assemble seperate hemisphere arrays into lh+rh arrays
    pial_points = np.array([*rh_pial_points, *lh_pial_points])
    curv_points = np.array([*rh_curv_points, *lh_curv_points])
    sulc_points = np.array([*rh_sulc_points, *lh_sulc_points])
    annot_points = np.array([*rh_annot_points, *lh_annot_points])

    # Create new array for vertex selection
    include_vertices = np.ones(np.shape(curv_points), dtype=bool)

    # Find indices of vertices which exceed the threshold for curv/sulc
    for surf, threshold, sign in [
        (sulc_points, threshold_sulc, -1), (curv_points, threshold_curv, -1)
    ]:
        abs_threshold = np.mean(surf) + threshold * np.std(surf)

        include_vertices[surf * sign < abs_threshold * sign] = False
        include_vertices[surf == 0.0] = False

    # Extract frontal lobe indices
    frontal_vertices = np.zeros(np.shape(include_vertices), dtype=bool)
    labels_frontal = [3, 27, 28]

    for label in labels_frontal:
        frontal_vertices[annot_points == label] = True

    include_vertices[~frontal_vertices] = False

    # Delete all vertices which do not conform to specs
    entry_points_ras = pial_points[include_vertices]

    # Transform entry point coordinates from RAS to voxel space
    ras2vox_aff = np.linalg.inv(mgh_header.get_vox2ras_tkr())

    entry_points_vox = np.zeros(np.shape(entry_points_ras))
    for i in range(np.shape(entry_points_vox)[0]):
        entry_points_vox[i] = (
            ras2vox_aff.dot(np.array([*entry_points_ras[i], 1]))
        )[:-1].astype(int)

    # Convert entry point list to mask
    for i in range(np.shape(entry_points_vox)[0]):
        indices = entry_points_vox[i].astype(int)
        mask[indices[0], indices[1], indices[2]] = 1.0

    # Perform affine transform to subject space
    if not (aff_fs == aff).all():
        aff_translation = (np.linalg.inv(aff_fs)).dot(aff)
        mask = affine_transform(
            mask, aff_translation,
            output_shape=np.shape(nogo_np)
        )

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
    mask[nogo_mask < 1e-2] = 0.0

    # Import BET image to numpy
    bet_img, aff_bet, _ = \
        load_nifti(processing_paths["bet_path"])

    # Perform affine transform (if applicable)
    if not (aff_bet == aff).all():
        aff_translation = (np.linalg.inv(aff_bet)).dot(aff)
        bet_img = affine_transform(
            bet_img, aff_translation,
            output_shape=np.shape(mask)
        )

    # Binarize BET image
    bet_mask = np.zeros(np.shape(bet_img))
    bet_mask[bet_img > 1e-2] = 1.0

    # Calculate distance map to edge of the brain
    distance_map = generate_distance_map(1 - bet_mask, aff, 15)

    # If an entry point is situated too far from the brain surface,
    # omit it. "Too far" is defined as 15 mm
    mask[distance_map >= 15.0] = 0.0

    # # Save mask
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
            "lh_pial_path":
                os.path.join(paths["fs_paths"][subject], "surf", "lh.pial.T1"),
            "rh_pial_path":
                os.path.join(paths["fs_paths"][subject], "surf", "rh.pial.T1"),
            "lh_curv_path":
                os.path.join(paths["fs_paths"][subject], "surf", "lh.curv"),
            "rh_curv_path":
                os.path.join(paths["fs_paths"][subject], "surf", "rh.curv"),
            "lh_sulc_path":
                os.path.join(paths["fs_paths"][subject], "surf", "lh.sulc"),
            "rh_sulc_path":
                os.path.join(paths["fs_paths"][subject], "surf", "rh.sulc"),
            "orig_path":
                os.path.join(paths["fs_paths"][subject], "mri", "orig.mgz"),
            "lh_annot_path":
                os.path.join(paths["fs_paths"][subject],
                             "label", "lh.aparc.annot"),
            "rh_annot_path":
                os.path.join(paths["fs_paths"][subject],
                             "label", "rh.aparc.annot"),
            "fs_labels_path":
                seg_paths["fs_labels"],
            "nogo_mask":
                seg_paths["sulcus_mask"],
            "bet_path":
                paths["fsl_paths"][subject]["bet"],
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
