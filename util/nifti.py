import nibabel as nib


def load_nifti(path):
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
