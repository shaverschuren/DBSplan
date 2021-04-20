import sys
if "" not in sys.path : sys.path.append("")
if "src" not in sys.path : sys.path.append("src")

import os
import json
import nibabel
import util.general


def main(config_path):
    """
    Main function for the DBSplan software pipeline.
    TODO: Parameters to pass + processing steps etc. (Might do this in bash eventually)
    """

    # Determine OS
    os_str = util.general.check_os()
    
    # Extract config data
    config_data = util.general.extract_json(config_path)


if __name__ == "__main__":
    main("config.json")
