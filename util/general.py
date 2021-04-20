import sys


def check_os():
    """
    This function checks the operating system of the current machine.
    It outputs a string, being either 'lnx' : Linux, 'win' : Windows, 'mac' : MacOS.
    Other operating systems are not supported. 
    """
    
    if sys.platform.startswith('win32'):
        os_str = "win"
    elif sys.platform.startswith('linux'):
        os_str = "lnx"
    elif sys.platform.startswith('darwin'):
        os_str = "mac"
    else:
        raise ValueError(f"Operating System ({sys.platform}) not supported.")

    return os_str