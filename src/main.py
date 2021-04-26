import sys
if "" not in sys.path : sys.path.append("")
if "src" not in sys.path : sys.path.append("src")

from initialization import initialization
from preprocessing import preprocessing
from segmentation import segmentation
from registration import registration


def main():
    """
    Main function for the DBSplan software pipeline.
    """

    # Initialize the pipeline
    paths, settings = initialization()

    # MODULE 1 : PREPROCESSING
    paths, settings = preprocessing(paths, settings)

    # MODULE 2 : SEGMENTATION
    paths, settings = segmentation(paths, settings)

    # MODULE 3 : REGISTRATION
    paths, settings = registration(paths, settings)

if __name__ == "__main__":
    main()
