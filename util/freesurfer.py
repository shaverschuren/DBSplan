"""Utility module for basic FreeSurfer-related functions"""

import os
import subprocess
from typing import Union


def mgz2nii(mgz_path: str, nii_path: str):
    """
    This function performs an mgz to nii conversion.
    It uses the FreeSurfer software package for this
    purpose.
    """

    # Assemble command
    command = ["mri_convert",
               "--in_type", "mgz",
               "--out_type", "nii",
               mgz_path,
               nii_path]

    # Open stream and pass command
    recon_stream = subprocess.Popen(command, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
    # Read output
    msg, error = recon_stream.communicate()
    # End stream
    recon_stream.terminate()

    if error:
        raise UserWarning("Fatal error occured during command-line FreeSurfer"
                          " usage.\nExited with error message:\n"
                          f"{error.decode('utf-8')}")


def extract_tissues(aparc_aseg_path: str, mask_path: str,
                    tissue_labels: Union[list, str, int]):
    """
    This function extracts tissues from the aparc+aseg.mgz file
    and outputs the binary mask to a given file in nifti format.
    The given tissue labels may either be a single label (str or int)
    or a list of labels (list(str or int)), as are given in the
    FreeSurfer documentation and as labels in the aparc+aseg.mgz file.
    """

    # Check tissue_labels parameter
    if type(tissue_labels) == list:
        labels_list: list = list([*tissue_labels])
    elif type(tissue_labels) in [str, int]:
        labels_list: list = list([tissue_labels])
    else:
        raise TypeError("The value of 'tissue_labels' must be either"
                        " a list, a string or an integer.")

    # Build intermediate mgz mask file path
    if mask_path.endswith(".nii.gz"):
        mask_mgz_path = mask_path[:-7] + ".mgz"
    elif mask_path.endswith(".nii"):
        mask_mgz_path = mask_path[:-4] + ".mgz"
    else:
        raise ValueError("mask_path must be a nifti file path.")

    # Assemble command
    command = ["mri_binarize",
               "--i", aparc_aseg_path,
               "--o", mask_mgz_path]

    for label in labels_list:
        extension = ["--match", str(label)]
        command.extend(extension)

    # Open stream and pass command
    recon_stream = subprocess.Popen(command, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
    # Read output
    msg, error = recon_stream.communicate()
    # End stream
    recon_stream.terminate()

    if error:
        raise UserWarning("Fatal error occured during command-line FreeSurfer"
                          " usage.\nExited with error message:\n"
                          f"{error.decode('utf-8')}")

    # Convert mgz mask to nii mask and remove tmp file
    mgz2nii(mask_mgz_path, mask_path)
    os.remove(mask_mgz_path)
