import subprocess


def check_fsl():
    """
    This function checks for the correct installation of freesurfer.
    It does so by calling 'freesurfer' to the main terminal
    and checking for errors.
    """

    # Initialize test vars
    test_ok = True
    error_msg = ""

    # Define test commands
    test_commands = ["flirt", "bet"]

    # Iteratively run test commands
    for command in test_commands:
        # Open stream and pass a test command command
        check_stream = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Read output
        _, error = check_stream.communicate()
        # End stream
        check_stream.terminate()
        # If there was an error, update test_ok var
        if error: 
            test_ok = False
            error_msg = error_msg + error.decode("utf-8")

    # If there was an error in any of the tests, raise a warning.
    if test_ok:
        return True
    else:
        raise UserWarning(  "FSL is not installed correctly." \
                            "\nPlease check https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation " \
                            "for elaboration on the installation process." \
                            f"\nSystem error message:\n{error_msg}")


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
