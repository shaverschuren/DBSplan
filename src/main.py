import sys
if "" not in sys.path : sys.path.append("")
if "src" not in sys.path : sys.path.append("src")

import os
import util.general


def main():
    """
    Main function for the DBSplan software pipeline.
    TODO: Parameters to pass + processing steps etc. (Might do this in bash eventually)
    """

    os_str = util.general.check_os()


if __name__ == "__main__":
    main()
