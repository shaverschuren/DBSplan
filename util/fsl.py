"""Utility module for basic FSL-related functions"""

import subprocess
from typing import Optional


def flirt_registration(in_path: str, ref_path: str, out_path: str,
                       init_path: Optional[str] = None,
                       omat_path: Optional[str] = None,
                       apply_xfm: bool = False, dof: Optional[int] = 6):
    """
    This function performs a simple affine registration with
    'dof' degrees of freedom of an image at 'in_path' to an image
    at 'ref_path' to create a final registered image at 'out_path'.
    The transformation matrix may be stored at 'omat_path', yet this is
    optional. Also, an initial transformation may be chosen at 'init_path'.
    Choose 'apply_xfm' = True for the simple application of this transformation
    without any optimisation.
    """

    # Assemble command
    command = ["flirt",
               "-in", in_path,
               "-ref", ref_path,
               "-out", out_path]

    if omat_path:
        command.extend(["-omat", omat_path])
    if init_path:
        command.extend(["-init", init_path])
    if apply_xfm:
        command.append("-applyxfm")
    if dof:
        command.extend(["-dof", str(dof)])

    # Open stream and pass command
    recon_stream = subprocess.Popen(command, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
    # Read output
    msg, error = recon_stream.communicate()
    # End stream
    recon_stream.terminate()

    if error:
        raise UserWarning("Fatal error occured during command-line FLIRT"
                          " usage.\nExited with error message:\n"
                          f"{error.decode('utf-8')}")
