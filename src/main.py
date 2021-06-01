"""DBSplan - Main module

This module simply runs through the entire
DBSplan pipeline. One may call it by running `main`.
Settings are provided in the `config.json` file.
"""

# Path setup
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(root, "src")
if root not in sys.path: sys.path.append(root)
if src not in sys.path: sys.path.append(src)

# File-specific imports
from initialization import initialization           # noqa: E402
from preprocessing import preprocessing             # noqa: E402
from registration_mri import registration_mri       # noqa: E402
from segmentation import segmentation               # noqa: E402
from registration_ct import registration_ct         # noqa: E402
from path_planning import path_planning             # noqa: E402


def main():
    """
    Main function for the DBSplan software pipeline.
    """

    # Setup config path
    config_path = os.path.join(root, "config.json")

    # Initialize the pipeline
    paths, settings = initialization(config_path)

    # MODULE 1 : PREPROCESSING
    paths, settings = preprocessing(paths, settings)

    # MODULE 2 : MRI COREGISTRATION
    paths, settings = registration_mri(paths, settings)

    # MODULE 3 : SEGMENTATION
    paths, settings = segmentation(paths, settings)

    # MODULE 4 : CT COREGISTRATION
    paths, settings = registration_ct(paths, settings)

    # MODULE 5 : PATH PLANNING
    paths, settings = path_planning(paths, settings)


if __name__ == "__main__":
    main()
