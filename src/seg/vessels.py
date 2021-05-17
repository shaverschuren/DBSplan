import os


def seg_vessels(paths, settings, verbose=True):
    """
    This function performs the vessel segmentation.
    """

    # Initialize skipped_img variable
    skipped_img = False

    # If applicable, make segmentation paths and folder
    if "segDir" not in paths:
        paths["segDir"] = os.path.join(paths["tmpDataDir"], "segmentation")
    if "seg_paths" not in paths:
        paths["seg_paths"] = {}

    if not os.path.isdir(paths["segDir"]): os.mkdir(paths["segDir"])

    # Perform the actual vessel extraction/segmentation
    print("TODO: Implement vessel segmentation")

    # If some files were skipped, write message
    if verbose and skipped_img:
        print("Some scans were skipped due to the output being complete.\n"
              "If you want to rerun this entire module, please set "
              "'resetModules'[1] to 0 in the config.json file.")

    return paths, settings
