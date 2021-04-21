import sys
if "" not in sys.path : sys.path.append("")
if "src" not in sys.path : sys.path.append("src")

from initialization import initialization
from preprocessing import preprocessing


def registration(paths, settings, verbose=True):
    """
    This is the main wrapper function for the registration module.
    It calls on other functions to perform specific tasks.
    """
    # TODO: Implement everything

    return paths, settings


if __name__ == "__main__":
    registration(*preprocessing(*initialization()))