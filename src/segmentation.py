"""DBSplan - Segmentation module

This module performs several tasks, which may all
be called from the `segmentation` function. Specific
tasks are imported from the `seg` module.
- Run FSL processing (https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/)
- Segment ventricles -> seg.ventricles
- Segment sulci -> seg.sulci
- Segment vessels -> seg.vessels
- Segment entry points -> seg.entry_points
"""

# Path setup
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(root, "src")
if root not in sys.path: sys.path.append(root)
if src not in sys.path: sys.path.append(src)

# File-specific imports
import numpy as np                                      # noqa: E402
import nibabel as nib                                   # noqa: E402
from scipy.ndimage import affine_transform              # noqa: E402
from initialization import initialization               # noqa: E402
from preprocessing import preprocessing                 # noqa: E402
from registration_mri import registration_mri           # noqa: E402
from seg.fsl import generate_fsl_paths, process_fsl     # noqa: E402
from seg.ventricles import seg_ventricles               # noqa: E402
from seg.sulci import seg_sulci                         # noqa: E402
from seg.vessels import seg_vessels                     # noqa: E402
from seg.entry_points import seg_entry_points           # noqa: E402
from util.style import print_header, print_result       # noqa: E402
from util.general import log_dict                       # noqa: E402
from util.nifti import load_nifti                       # noqa: E402


def finalize_segmentation(paths: dict, settings: dict, verbose: bool = True) \
        -> tuple[dict, dict]:
    """
    This function finalizes the segmentation module.
    It performs a few tasks:
    - Firstly, we check for all the files and make sure everything is
    there.
    - Then, we combine the ventricle, sulcus and vessel masks
    into one final mask.
    """

    # Define all required items for paths dict
    required_paths = ["dir", "fs_labels", "ventricle_mask",
                      "sulcus_mask", "vessel_mask"]

    # Loop through all subjects
    for subject, subject_paths in paths["seg_paths"].items():

        # Now, check whether all relevant files are there
        dict_ok = all(
            (item in subject_paths) for item in required_paths
        )

        files_ok = all(
            os.path.exists(path) for (_, path) in subject_paths.items()
        )

        if (not dict_ok) or (not files_ok):
            raise UserWarning(
                "Segmentation paths/files are not complete for subject "
                f"{subject:s}!"
                "\nPlease try to rerun the segmentation module, "
                "e.g. by removing tmpDir/segmentation or by setting "
                "resetModules[2] to 1 in the config.json file."
            )

        # Define final mask path
        mask_path = os.path.join(subject_paths["dir"], "final_mask.nii.gz")
        paths["seg_paths"][subject]["final_mask"] = mask_path

        # If it doesn't already exist, combine masks
        if not os.path.exists(mask_path):
            # Now, load all partial masks
            ventricle_mask, vent_aff, _ = \
                load_nifti(subject_paths["ventricle_mask"])
            sulcus_mask, sulc_aff, _ = \
                load_nifti(subject_paths["sulcus_mask"])
            vessel_mask, vess_aff, hdr = \
                load_nifti(subject_paths["vessel_mask"])
            entry_mask, entr_aff, _ = \
                load_nifti(subject_paths["entry_points"])

            # Transform all masks to appropriate space
            sulc_translation = (np.linalg.inv(sulc_aff)).dot(vess_aff)
            vent_translation = (np.linalg.inv(vent_aff)).dot(vess_aff)
            entr_translation = (np.linalg.inv(entr_aff)).dot(vess_aff)

            sulcus_mask = affine_transform(
                sulcus_mask, sulc_translation,
                output_shape=np.shape(vessel_mask)
            )
            ventricle_mask = affine_transform(
                ventricle_mask, vent_translation,
                output_shape=np.shape(vessel_mask)
            )
            entry_mask = affine_transform(
                entry_mask, entr_translation,
                output_shape=np.shape(vessel_mask)
            )

            shapes_ok = (
                (np.shape(ventricle_mask) == np.shape(sulcus_mask)) and
                (np.shape(sulcus_mask) == np.shape(vessel_mask))
            )
            if shapes_ok:
                final_mask = np.zeros(np.shape(vessel_mask))
            else:
                raise ValueError(
                    "The intermediate masks are not the same size!"
                    f"\nVentricle mask: {np.shape(ventricle_mask)}"
                    f"\nSulcus mask:    {np.shape(sulcus_mask)}"
                    f"\nVessel mask:    {np.shape(vessel_mask)}"
                )

            # Rebinarize ventricle/sulcus/entry masks
            ventricle_mask[ventricle_mask >= 0.5] = 1.0
            ventricle_mask[ventricle_mask < 0.5] = 0.0

            sulcus_mask[sulcus_mask >= 0.5] = 1.0
            sulcus_mask[sulcus_mask < 0.5] = 0.0

            entry_mask[entry_mask >= 0.5] = 1.0
            entry_mask[entry_mask < 0.5] = 0.0

            # Combine masks
            final_mask[ventricle_mask > 1e-1] = 1.0
            final_mask[sulcus_mask > 1e-1] = 1.0
            final_mask[vessel_mask > 1e-1] = 1.0

            # Re-save ventricle/sulcus/entry masks in FSL orientation instead
            # of FreeSurfer. This enables later co-registration to
            # other images.

            nib.save(nib.Nifti1Image(ventricle_mask, vess_aff, hdr),
                     subject_paths["ventricle_mask"])
            nib.save(nib.Nifti1Image(sulcus_mask, vess_aff, hdr),
                     subject_paths["sulcus_mask"])
            nib.save(nib.Nifti1Image(entry_mask, vess_aff, hdr),
                     subject_paths["entry_points"])

            # Save final mask
            nii_mask = nib.Nifti1Image(final_mask, vess_aff, hdr)
            nib.save(nii_mask, mask_path)

    return paths, settings


def segmentation(paths: dict, settings: dict, verbose: bool = True) \
        -> tuple[dict, dict]:
    """
    This is the main wrapper function for the segmentation module.
    It calls on other functions to perform specific tasks.
    """

    if verbose: print_header("\n==== MODULE 2 - SEGMENTATION ====")

    # Check whether module should be run (from config file)
    if settings["runModules"][2] == 0:
        # Skip module
        _, paths = generate_fsl_paths(paths, settings)
        if verbose: print("\nSKIPPED:\n"
                          "'run_modules'[2] parameter == 0.\n"
                          "Assuming all data is already segmented.\n"
                          "Skipping segmentation process. "
                          "Added expected paths to 'paths'.")

    elif settings["runModules"][2] == 1:
        # Run module

        if verbose: print("\nRunning FSL BET/FAST...")
        paths, settings = process_fsl(paths, settings, verbose)
        if verbose: print("FSL BET/FAST completed!")

        if verbose: print("\nPerforming ventricle segmentation...")
        paths, settings = seg_ventricles(paths, settings, verbose)
        if verbose: print("Ventricle segmentation completed!")

        if verbose: print("\nPerforming sulcus segmentation...")
        paths, settings = seg_sulci(paths, settings, verbose)
        if verbose: print("Sulcus segmentation completed!")

        if verbose: print("\nPerforming vessel segmentation...")
        paths, settings = seg_vessels(paths, settings, verbose)
        if verbose: print("Vessel segmentation completed!")

        if verbose: print("\nPerforming entry point segmentation...")
        paths, settings = seg_entry_points(paths, settings, verbose)
        if verbose: print("Entry point segmentation completed!")

        if verbose: print(
            "\nPerforming mask combination and restructuring... ",
            end="", flush=True
        )
        paths, settings = finalize_segmentation(paths, settings, verbose)
        if verbose: print_result()

        if verbose: print_header("\nSEGMENTATION FINISHED")

    else:
        raise ValueError("parameter run_modules should be a list "
                         "containing only 0's and 1's. "
                         "Please check the config file (config.json).")

    # Log paths and settings
    log_dict(paths, os.path.join(paths["logsDir"], "paths.json"))
    log_dict(settings, os.path.join(paths["logsDir"], "settings.json"))

    return paths, settings


if __name__ == "__main__":
    paths, settings = registration_mri(*preprocessing(*initialization()))
    segmentation(paths, settings)
