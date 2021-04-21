import sys
if "" not in sys.path : sys.path.append("")
if "src" not in sys.path : sys.path.append("src")

import os
from tqdm import tqdm
from initialization import initialization
from util.style import print_header, print_result
from util.general import extract_json


def generate_process_paths(paths, settings):
    """
    This function generates an array of strings (paths). 
    It contains all paths required for the preprocessing process.
    We'll use info from dicts 'paths' and 'settings'.
    """

    # Initialize paths array and new data field the for paths dict
    process_paths = []
    paths["nii_paths"] = {}
    paths["dcm_paths"] = {}

    # Extract data from the usedScans.json file
    usedScans_file = os.path.join(paths["projectDir"], settings["usedScans_file"])
    dcmPaths_dict = extract_json(usedScans_file)

    # Loop over scan types (T1w, T1w-GADO and CT)
    for scanType, pathArray in dcmPaths_dict.items():
        # Loop over subjects, dcm paths
        for subject, path in pathArray.items():
            # Find paths for the actual dcm folder and to-be-created nifti-file
            if type(path) in [list, str]:
                dcm_path = os.path.join(paths["source_dcm"][subject], *path)
                nii_path = os.path.join(paths["sourcedataDir"], "nifti", subject, scanType + ".nii")

                if os.path.exists(dcm_path):
                    # Add paths to path array
                    process_paths.append([dcm_path, nii_path])

                    # Add nii path to paths dict
                    if subject not in paths["nii_paths"]: paths["nii_paths"][subject] = {}
                    paths["nii_paths"][subject][scanType] = nii_path
                    # Add dcm path to paths dict
                    if subject not in paths["dcm_paths"]: paths["dcm_paths"][subject] = {}
                    paths["dcm_paths"][subject][scanType] = dcm_path
                else:
                    raise ValueError(f"Dicom path '{dcm_path}' doesn't exist.")
            else:
                pass

    return process_paths, paths


def dcm2nii(process_paths, paths, settings, verbose=True):
    """
    This function performs the actual dicom to nifti conversion.
    It makes use of the external program dcm2nii for this purpose.
    """
    # Initialize logs string
    log_str = ""

    # Define iterator
    if verbose:
        iterator = tqdm(range(len(process_paths)), ascii=True, bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}')
    else:
        iterator = range(len(process_paths))

    # Loop over the dcm,nii path pairs and perform the conversion.
    for img_i in iterator:
        # Extract paths from array
        dcm_path, nii_path = process_paths[img_i]

        # Check whether output folder exists and if not, make it
        output_folder = os.path.dirname(nii_path)
        if not os.path.isdir(output_folder) : os.mkdir(output_folder)

        # Check OS for command line implementation.
        if settings["OS"] == "win":
            dcm2nii_path = os.path.join("ext", "MRIcron", "dcm2nii.exe")
            quote = "\""
        elif settings["OS"] == "lnx":
            dcm2nii_path = os.path.join("ext", "MRIcron", "dcm2nii-lx64")
            quote = "\""
        elif settings["OS"] == "mac":
            dcm2nii_path = os.path.join("ext", "MRIcron", "dcm2nii-osx")
            quote = "\'\'"
        else:
            raise UserWarning("Operating system not supported (or value of settings['OS'] is wrong).")

        # Assemble command
        command =   f'{dcm2nii_path} ' \
                    f'-f {quote}{os.path.splitext(os.path.split(nii_path)[-1])[0]}{quote} ' \
                    f'-p y -z y ' \
                    f'-o {quote}{os.path.dirname(nii_path)}{quote} ' \
                    f'{quote}{dcm_path}{quote}'
        
        # Give the command and read the output (store as logs)
        cmd_stream = os.popen(command)
        output = cmd_stream.read()

        img_log =   "------------------------------------------------------" \
                    f"\nDICOM path: {dcm_path}" \
                    f"\nNIFTI path: {nii_path}" \
                    + "\n\n" + output + "\n\n"

        log_str = log_str + img_log

    # Write logs to text file
    logs_path = os.path.join(paths["logsDir"], "dcm2nii_logs.txt")
    logs_file = open(logs_path, "w")
    logs_file.write(log_str)
    logs_file.close()


def preprocessing(paths, settings, verbose=True):
    """
    This function is the main function for the preprocessing step.
    It calls on other functions to perform some tasks, such as:
    - DICOM - NIFTI conversion
    - File structure management
    """

    if verbose : print_header("\n==== MODULE 1 - PREPROCESSING ====")

    # Check whether module should be run (from config file)
    if settings["run_modules"][0] == 0:
        # Skip module
        if verbose : print("Skipped module...")
    elif settings["run_modules"][0] == 1:   
        # Run module

        # Firstly, check which scans will have to be processed.
        if verbose : print("\nGenerating processing paths...\t", end="", flush=True)
        process_paths, paths = generate_process_paths(paths, settings)
        if verbose : print_result()

        # Now, Perform the dcm2nii file conversion.
        if verbose : print("\nPerforming dcm2nii conversion...")
        dcm2nii(process_paths, paths, settings, verbose)
        if verbose : print("dcm2nii conversion completed!")

        if verbose : print_header("\nPREPROCESSING FINISHED")
        return paths, settings

    else:
        raise ValueError("parameter run_modules should be a list containing only 0's and 1's. " \
                        "Please check the config file (config.json).")


if __name__ == "__main__":
    preprocessing(*initialization())