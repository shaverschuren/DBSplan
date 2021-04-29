import sys
import json


def append_logs(msg, file, mode="a"):
    """
    This function is used for appending log files.
    """
    logs_file = open(file, mode)
    logs_file.write(msg)
    logs_file.close()


def check_type(var, var_type):
    """
    This function checks whether a variable is of the appropriate type.
    If not, it generates an error of sorts.
    """

    # Determine the actual variable type
    act_type = type(var)

    # Check whether the actual type matches the wanted type
    if var_type != act_type:
        raise TypeError("Variable is not of the appropriate type."
                        f"Should be {var_type}, not {act_type}")
    else:
        return True


def check_os():
    """
    This function checks the operating system of the current machine.
    It outputs a string, being either
    'lnx' : Linux, 'win' : Windows, 'mac' : MacOS.
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

        if verbose: print(data)

        return data
