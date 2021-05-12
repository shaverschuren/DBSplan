# Path setup
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(root, "src")
if root not in sys.path: sys.path.append(root)
if src not in sys.path: sys.path.append(src)

# File-specific imports
from initialization import initialization   # noqa: E402
from preprocessing import preprocessing     # noqa: E402
from segmentation import segmentation       # noqa: E402
from registration import registration       # noqa: E402


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

    # MODULE 2 : SEGMENTATION
    paths, settings = segmentation(paths, settings)

    # MODULE 3 : REGISTRATION
    paths, settings = registration(paths, settings)


if __name__ == "__main__":
    main()
