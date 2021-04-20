import sys
import json


def print_result(succeeded=True):

    if succeeded:
        print("\033[92mOK\033[0m")
    elif not succeeded:
        print("\033[91mFAIL\033[0m")
    else:
        raise ValueError("Parameter 'succeeded' should be a boolean")
    
    return


class print_style:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


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
        raise ValueError(f"\nOperating System ({sys.platform}) not supported.")

    return os_str


def extract_json(json_path, verbose=False):
    """
    This function is used for extracting data from .json files.
    Primarily, it is used for extracting config file data.
    """

    if not json_path.endswith('.json'):
        raise ValueError("\nThe config file should be of the .json type")
    else:
        with open(json_path) as json_data_file:
            data = json.load(json_data_file)

        if verbose : print(data)

        return data
    