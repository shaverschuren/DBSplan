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


def print_result(succeeded: bool = True):

    if succeeded:
        print("\033[92mOK\033[0m")
    elif not succeeded:
        print("\033[91mFAIL\033[0m")
    else:
        raise ValueError("Parameter 'succeeded' should be a boolean")

    return


def print_header(message: str):
    print(print_style.BOLD + message + print_style.END)
