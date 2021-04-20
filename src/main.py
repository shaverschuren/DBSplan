import sys
if "" not in sys.path : sys.path.append("")
if "src" not in sys.path : sys.path.append("src")

from initialization import initialize
from preprocessing import preprocessing


def main():
    """
    Main function for the DBSplan software pipeline.
    """

    # Initialize the pipeline
    paths, settings = initialize()

    # MODULE 1 : PREPROCESSING
    preprocessing(paths, settings)

if __name__ == "__main__":
    main()
