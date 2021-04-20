import sys
import json


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


def extract_json(json_path, verbose=False):
    """
    This function is used for extracting data from .json files.
    Primarily, it is used for extracting config file data.
    """
    with open(json_path) as json_data_file:
        data = json.load(json_data_file)

    if verbose : print(data)

    return data