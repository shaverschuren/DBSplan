"""DBSplan - Path Planning module

This module performs several tasks, which may all
be called from the `path_planning` function.
- ...
- ...
"""

# Path setup
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(root, "src")
if root not in sys.path: sys.path.append(root)
if src not in sys.path: sys.path.append(src)

# File-specific imports
import numpy as np                          # noqa: E402
import math                                 # noqa: E402
from tqdm import tqdm                       # noqa: E402
import nibabel as nib                       # noqa: E402
import scipy.ndimage.morphology as morph    # noqa: E402
from util.style import print_header         # noqa: E402
from util.general import log_dict           # noqa: E402
from util.nifti import load_nifti           # noqa: E402


def generate_planning_paths(paths: dict, settings: dict) -> tuple[list, dict]:
    """
    This function generates the required processing paths
    for the path planning process.
    """

    # Create empty dicts
    paths["pathplanning_paths"] = {}
    planning_paths = []

    # Create relevant directory and add to paths
    path_planning_dir = os.path.join(paths["tmpDataDir"], "path_planning")
    if not os.path.exists(path_planning_dir): os.mkdir(path_planning_dir)

    paths["pathplanningDir"] = path_planning_dir

    # Loop over subjects and assemble appropriate paths
    for subject in paths["ctreg_paths"]:
        # Assemble and create subject directory (+ raw dir)
        subject_dir = os.path.join(path_planning_dir, subject)
        if not os.path.exists(subject_dir): os.mkdir(subject_dir)

        raw_dir = os.path.join(subject_dir, "raw")
        if not os.path.exists(raw_dir): os.mkdir(raw_dir)

        # Create output paths
        distance_map_combined_path = \
            os.path.join(raw_dir, "distance_map_combined.nii.gz")
        distance_map_ventricles_path = \
            os.path.join(raw_dir, "distance_map_ventricles.nii.gz")
        distance_map_sulci_path = \
            os.path.join(raw_dir, "distance_map_sulci.nii.gz")
        distance_map_vessels_path = \
            os.path.join(raw_dir, "distance_map_vessels.nii.gz")

        output_txt = os.path.join(subject_dir, "path.txt")

        # Assemble subject path dict
        subject_dict = {
            "dir": subject_dir,
            "raw": raw_dir,
            "CT": paths["nii_paths"][subject]["CT_PRE"],
            "T1w": paths["ctreg_paths"][subject]["T1w_coreg"],
            "T1w_gado": paths["ctreg_paths"][subject]["gado_coreg"],
            "final_mask":
                paths["ctreg_paths"][subject]["mask_final_coreg"],
            "ventricle_mask":
                paths["ctreg_paths"][subject]["mask_ventricles_coreg"],
            "sulcus_mask":
                paths["ctreg_paths"][subject]["mask_sulci_coreg"],
            "vessel_mask":
                paths["ctreg_paths"][subject]["mask_vessels_coreg"],
            "entry_point_mask":
                paths["ctreg_paths"][subject]["entry_points_coreg"],
            "distance_map_combined": distance_map_combined_path,
            "distance_map_ventricles": distance_map_ventricles_path,
            "distance_map_sulci": distance_map_sulci_path,
            "distance_map_vessels": distance_map_vessels_path,
            "output_path": output_txt
        }

        # Add subject dict to paths + planning paths
        planning_paths.append(subject_dict)
        paths["pathplanning_paths"][subject] = subject_dict

    return planning_paths, paths


def generate_distance_map(mask: np.ndarray, aff: np.ndarray,
                          cutoff: float = 15.0) -> np.ndarray:
    """
    This function generates a distance map from a mask.
    This map represents the distance between any voxel and
    a structure which must not be hit. If the voxel is within the
    voxel that shouldn't be hit, the value becomes 0.
    The maximum distance is capped (by default at 15 (mm) ) to
    deal with the problem of huge values at the edge of the image.
    """

    # Calculate voxel size
    vox_dim = np.mean(np.absolute((aff.diagonal())[:-1]))

    # Generate distance map
    distance_map = morph.distance_transform_edt(1 - mask) * vox_dim

    distance_map[distance_map > cutoff] = cutoff

    return distance_map


def generate_entry_points(subject_paths: dict, n_points: int = 10000) \
        -> np.ndarray:
    """
    This function generates a list of entry points which may be
    explored in the path planning process. For the entry points,
    we will be taking a number of points of the frontal lobe gyri.
    These gyri have been previously segmented in the `segmentation`
    module, more specifically in the `seg.entry_points` module.
    In this function, we generate a list of points based on
    this segmentation.
    """

    # Import Entry point mask to numpy
    entry_point_mask, _, _ = load_nifti(subject_paths["entry_point_mask"])

    # Extract indices of entry points
    entry_points = np.swapaxes(np.nonzero(entry_point_mask), 0, 1)

    # Now, downsample this list to the required number of points
    # Here, we make use of the fact that nearby points are next to
    # each other in this list.
    entry_points_down = np.zeros((n_points, 3), dtype=int)

    for i in range(n_points):
        # Find index of sampled point in original entry point array
        point_id = math.floor(len(entry_points) / n_points) * i
        # Append downsampled array
        entry_points_down[i, :] = entry_points[point_id, :]

    return entry_points_down


def generate_trajectory(subject_paths: dict):
    """
    This function generates an appropriate trajectory
    for a certain subject. We use the paths generated by
    `generate_planning_paths` as pointers to the appropriate
    files.
    """

    # Load relevant files / images
    ct_np, aff_ct, _ = load_nifti(subject_paths["CT"])
    gado_np, aff_gado, _ = load_nifti(subject_paths["T1w_gado"])

    mask_combined, aff_mask_combined, hdr_mask = \
        load_nifti(subject_paths["final_mask"])
    mask_ventricles, aff_mask_ventricles, _ = \
        load_nifti(subject_paths["ventricle_mask"])
    mask_sulci, aff_mask_sulci, _ = \
        load_nifti(subject_paths["sulcus_mask"])
    mask_vessels, aff_mask_vessels, _ = \
        load_nifti(subject_paths["vessel_mask"])

    # Create and save distance maps
    for mask, aff, path_pointer in [
        (mask_combined, aff_mask_combined, "combined"),
        (mask_ventricles, aff_mask_ventricles, "ventricles"),
        (mask_sulci, aff_mask_sulci, "sulci"),
        (mask_vessels, aff_mask_vessels, "vessels"),
    ]:
        distance_map = generate_distance_map(mask, aff)
        nib.save(nib.Nifti1Image(distance_map, aff, hdr_mask),
                 subject_paths["distance_map_" + path_pointer])

    # Generate entry points
    entry_points = generate_entry_points(subject_paths)


def run_path_planning(paths: dict, settings: dict, verbose: bool = True) \
        -> tuple[dict, dict]:
    """
    This funcion runs the actual path planning process.
    It calls upon `generate_planning_paths` to generate the
    appropriate paths to use for the planning process. Additionally,
    it calls upon `generate_trajectory` to generate an appropriate
    trajectory for a specific patient.
    """

    # Initialize skipped_img
    skipped_img = False

    # Extract proper processing paths
    planning_paths, paths = generate_planning_paths(paths, settings)

    # Define iterator
    if verbose:
        iterator = tqdm(planning_paths, ascii=True,
                        bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}')
    else:
        iterator = planning_paths

    # Main loop
    for sub_paths in iterator:
        # Check whether output already there
        output_ok = os.path.exists(sub_paths["output_path"])

        # Determine whether to skip subject
        if output_ok:
            if settings["resetModules"][4] == 0:
                skipped_img = True
                continue
            elif settings["resetModules"][4] == 1:
                # Generate trajectory
                generate_trajectory(sub_paths)
            else:
                raise ValueError("Parameter 'resetModules' should be a list "
                                 "containing only 0's and 1's. "
                                 "Please check the config file (config.json).")
        else:
            # Generate trajectory
            generate_trajectory(sub_paths)

    # If some files were skipped, write message
    if verbose and skipped_img:
        print("Some scans were skipped due to the output being complete.\n"
              "If you want to rerun this entire module, please set "
              "'resetModules'[4] to 0 in the config.json file.")

    return paths, settings


def path_planning(paths: dict, settings: dict, verbose: bool = True)\
        -> tuple[dict, dict]:
    """
    This is the main wrapper function for the path planning module.
    It calls on other functions to perform specific tasks.
    """

    if verbose: print_header("\n==== MODULE 5 - PATH PLANNING ====")

    # Check whether module should be run (from config file)
    if settings["runModules"][4] == 0:
        # Skip module
        _, paths = generate_planning_paths(paths, settings)
        if verbose: print("\nSKIPPED:\n"
                          "'run_modules'[4] parameter == 0.\n"
                          "Assuming all data is already segmented.\n"
                          "Skipping segmentation process. "
                          "Added expected paths to 'paths'.")

    elif settings["runModules"][4] == 1:
        # Run module

        paths, settings = run_path_planning(paths, settings, verbose)

        if verbose: print_header("\nPATH PLANNING FINISHED")

    else:
        raise ValueError("parameter run_modules should be a list "
                         "containing only 0's and 1's. "
                         "Please check the config file (config.json).")

    # Log paths and settings
    log_dict(paths, os.path.join(paths["logsDir"], "paths.json"))
    log_dict(settings, os.path.join(paths["logsDir"], "settings.json"))

    return paths, settings
