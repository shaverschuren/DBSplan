import numpy as np
import nibabel as nib
import subprocess


def load_nifti(path: str) \
        -> tuple[np.ndarray, np.ndarray, nib.nifti1.Nifti1Header]:
    """
    This function loads a nifti image using
    the nibabel library.
    """
    # Extract image
    img = nib.load(path)
    img_aff = img.affine
    img_hdr = img.header
    # Extract the actual data in a numpy array
    data = img.get_fdata()

    return data, img_aff, img_hdr


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
               "--out_orientation", "RAS",
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
