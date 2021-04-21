import subprocess


def check_freesurfer():
    """
    This function checks for the correct installation of freesurfer.
    It does so by calling 'freesurfer' to the main terminal
    and checking for errors.
    """
    # Open stream and pass 'freesurfer' command
    check_stream = subprocess.Popen(['freesurfer'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Read output
    _, error = check_stream.communicate()
    # End stream
    check_stream.terminate()

    # If there was an error, raise a warning.
    if error:
        raise UserWarning(  "FreeSurfer is not installed correctly." \
                            "\nPlease check https://surfer.nmr.mgh.harvard.edu/fswiki/LinuxInstall " \
                            "for elaboration on the installation process." \
                            f"\nSystem error message:\n{error.decode('utf-8')}")
    else:
        return True