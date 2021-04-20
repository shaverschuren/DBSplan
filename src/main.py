import sys
if "" not in sys.path : sys.path.append("")
if "src" not in sys.path : sys.path.append("src")

from initialization import initialize


def main():
    """
    Main function for the DBSplan software pipeline.
    """

    # Initialize the pipeline
    paths = initialize()

if __name__ == "__main__":
    main()
