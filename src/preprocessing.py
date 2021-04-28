import sys
if "" not in sys.path : sys.path.append("")
if "src" not in sys.path : sys.path.append("src")

import os
from tqdm import tqdm
import shutil
import subprocess
from datetime import datetime
from initialization import initialization
from gui.ScanSelection import ScanSelection
from util.style import print_header, print_result


def generate_process_paths(paths, settings):
    """
    This function generates an array of strings (paths). 
    It contains all paths required for the preprocessing process.
    We'll use info from dicts 'paths' and 'settings'.
    """

    # Initialize paths array
    process_paths = []
    # Add new data fields for paths dict
    if "niiDir" not in paths : paths["niiDir"] = os.path.join(paths["tmpDataDir"], "nifti")
    if "fsDir" not in paths : paths["fsDir"] = os.path.join(paths["tmpDataDir"], "freesurfer")
    paths["nii_paths"] = {}
    paths["dcm_paths"] = {}
    paths["fs_paths"] = {}

    # Check for the existence of the "usedScans_file" parameter.
    # If it's there, use the file to find appropriate scans.
    # If not, start up a GUI to select the appropriate scans.
    if "usedScans" in settings:
        # Extract data from settings
        dcmPaths_dict = settings["usedScans"]

    else:
        # Fire up the scan selection GUI for choosing the appropiate scans.
        dcmPaths_dict = ScanSelection(paths, settings)

    # Loop over scan types (T1w, T1w-GADO and CT)
    for scanType, pathArray in dcmPaths_dict.items():
        # Loop over subjects, dcm paths
        for subject, path in pathArray.items():
            # Find paths for the actual dcm folder and to-be-created nifti-file
            if type(path) in [list, str]:
                dcm_path = os.path.join(paths["source_dcm"][subject], *path)
                nii_path = os.path.join(paths["niiDir"], subject, scanType + ".nii.gz")
                fs_path = os.path.join(paths["fsDir"], subject)

                if os.path.exists(dcm_path):
                    # Remove fs path for non-T1w without GADO
                    if scanType != "MRI_T1W":
                        fs_path = None
                    # Add paths to path array
                    process_paths.append([dcm_path, nii_path, fs_path])

                    # Add dcm path to paths dict
                    if subject not in paths["dcm_paths"]: paths["dcm_paths"][subject] = {}
                    paths["dcm_paths"][subject][scanType] = dcm_path
                    # Add nii path to paths dict
                    if subject not in paths["nii_paths"]: paths["nii_paths"][subject] = {}
                    paths["nii_paths"][subject][scanType] = nii_path
                    # Add fs path to paths dict
                    paths["fs_paths"][subject]= fs_path
                else:
                    raise ValueError(f"Dicom path '{dcm_path}' doesn't exist.")
            else:
                pass

    return process_paths, paths


def dcm2nii(process_paths, paths, settings, verbose=True):
    """
    This function performs the actual dicom to nifti conversion.
    It makes use of the external program dcm2nii for this purpose.
    If the output files are already there and resetModule is 0, 
    skip the file.
    """
    # Initialize logs string and skip label
    log_str = ""
    skipped_img = False

    # If applicable, make nifti directory
    if not os.path.isdir(paths["niiDir"]) : os.mkdir(paths["niiDir"])

    # Define iterator
    if verbose:
        iterator = tqdm(range(len(process_paths)), ascii=True, bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}')
    else:
        iterator = range(len(process_paths))

    # Loop over the dcm,nii path pairs and perform the conversion.
    for img_i in iterator:
        # Extract paths from array
        dcm_path, nii_path, _ = process_paths[img_i]

        # Check whether output folder exists and if not, make it.
        output_folder = os.path.dirname(nii_path)
        if not os.path.isdir(output_folder) : os.mkdir(output_folder)

        # Check whether all output files are already there
        if os.path.exists(nii_path) and os.path.exists(nii_path.replace(".nii.gz", ".json")):
            # If resetModules[0] is 0, skip this scan
            if settings["resetModules"][0] == 0:
                command = "---"
                output = "Output files are already there. Skipping..."
                skipped_img = True
                # Store output in logs (timed)
                now = datetime.now()
                img_log =   f"---------------- {now.strftime('%d/%m/%Y %H:%M:%S')} ----------------" \
                            f"\n{command}" \
                            f"\n\nDICOM path: {dcm_path}" \
                            f"\nNIFTI path: {nii_path}" \
                            + "\n\n" + output + "\n\n"
                log_str = log_str + img_log
                continue

            # If resetModules[0] is 1, remove output and redo conversion
            elif settings["resetModules"][0] == 1: 
                os.remove(nii_path)
                os.remove(nii_path.replace(".nii.gz", ".json"))

            # Other: Raise error
            else:
                raise ValueError(   "Parameter 'resetModules' should be a list containing only 0's and 1's. " \
                                    "Please check the config file (config.json).")

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
                    f'-f {quote}{os.path.split(nii_path)[-1][:-7]}{quote} ' \
                    f'-p y -z y ' \
                    f'-o {quote}{os.path.dirname(nii_path)}{quote} ' \
                    f'{quote}{dcm_path}{quote}'

        # Give the command and read the output (store as logs)
        cmd_stream = os.popen(command)
        output = cmd_stream.read()

        # Store output in logs (timed)
        now = datetime.now()
        img_log =   f"---------------- {now.strftime('%d/%m/%Y %H:%M:%S')} ----------------" \
                    f"\n{command}" \
                    f"\n\nDICOM path: {dcm_path}" \
                    f"\nNIFTI path: {nii_path}" \
                    + "\n\n" + output + "\n\n"

        log_str = log_str + img_log

    # Write logs to text file
    logs_path = os.path.join(paths["logsDir"], "dcm2nii_logs.txt")
    logs_file = open(logs_path, "w")
    logs_file.write(log_str)
    logs_file.close()

    # If some files were skipped, write message
    if verbose and skipped_img:
        print(  "Some scans were skipped due to the output being already there.\n" \
                "If you want to rerun this entire module, please set " \
                "'resetModules'[0] to 0 in the config.json file.")


def nii2fs(process_paths, paths, settings, verbose=True):
    """
    This function performs a dicom to freesurfer conversion.
    It makes use of the command line freesurfer application.
    """

    # Initialize logs string and skipped_img variable
    log_str = ""
    skipped_img = False

    # Remove irrelevant scans from list
    process_paths = [paths for paths in process_paths if paths[2] != None]

    # If applicable, make freesurfer directory
    if not os.path.isdir(paths["fsDir"]) : os.mkdir(paths["fsDir"])

    # Define iterator
    if verbose:
        iterator = tqdm(range(len(process_paths)), ascii=True, bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}')
    else:
        iterator = range(len(process_paths))

    # Loop over the dcm,nii path pairs and perform the conversion.
    for img_i in iterator:
        # Extract paths from array
        _, nii_path, fs_path = process_paths[img_i]

        if os.path.exists(fs_path):
            # If output folder already exists, skip this image
            if settings["resetModules"][0] == 0:
                command = "---"
                output = "Output files are already there. Skipping..."
                skipped_img = True
                # Store output in logs (timed)
                now = datetime.now()
                img_log =   f"---------------- {now.strftime('%d/%m/%Y %H:%M:%S')} ----------------" \
                            f"\n{command}" \
                            f"\n\nNIFTI path:\t\t{nii_path}" \
                            f"\nFreeSurfer path:\t{fs_path}" \
                            + "\n\n" + output + "\n\n"
                log_str = log_str + img_log
                continue

            # If output freesurfer folder already exists, remove it.
            elif settings["resetModules"][0] == 1:
                shutil.rmtree(fs_path)

            # Other: Raise error
            else:
                raise ValueError(   "Parameter 'resetModules' should be a list containing only 0's and 1's. " \
                                    "Please check the config file (config.json).")

        # Assemble command
        command = [ "recon-all", 
                    "-subjid", os.path.split(fs_path)[-1], 
                    "-i", nii_path, 
                    "-sd", paths["fsDir"],
                    "-3T",
                    "-autorecon1"]

        # Open stream and pass command
        recon_stream = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Read output
        msg, error = recon_stream.communicate()
        # End stream
        recon_stream.terminate()

        # Store output in logs (timed)
        now = datetime.now()
        img_log =   f"---------------- {now.strftime('%d/%m/%Y %H:%M:%S')} ----------------" \
                    f"\n{command}" \
                    f"\n\nNIFTI path:\t\t{nii_path}" \
                    f"\nFreeSurfer path:\t{fs_path}" \
                    f"\n\n{msg.decode('utf-8')}" \
                    f"\n{error.decode('utf-8')}\n\n"

        log_str = log_str + img_log

    # Write logs to text file
    logs_path = os.path.join(paths["logsDir"], "nii2freesurfer_logs.txt")
    logs_file = open(logs_path, "w")
    logs_file.write(log_str)
    logs_file.close()

    # If some files were skipped, write message
    if verbose and skipped_img:
        print(  "Some scans were skipped due to the output being already there.\n" \
                "If you want to rerun this entire module, please set " \
                "'resetModules'[0] to 0 in the config.json file.")


def preprocessing(paths, settings, verbose=True):
    """
    This function is the main function for the preprocessing step.
    It calls on other functions to perform some tasks, such as:
    - DICOM - NIFTI conversion
    - File structure management
    """

    if verbose : print_header("\n==== MODULE 1 - PREPROCESSING ====")

    # Check whether module should be run (from config file)
    if settings["runModules"][0] == 0:
        # Skip module
        if verbose : print( "\nSKIPPED:\n" \
                            "'runModules'[0] parameter == 0.\n" \
                            "Assuming all data is already preprocessed.\n" \
                            "Skipping module....")
        process_paths, paths = generate_process_paths(paths, settings)

    elif settings["runModules"][0] == 1:   
        # Run module

        # Firstly, check which scans will have to be processed.
        if verbose : print("\nGenerating processing paths...\t", end="", flush=True)
        process_paths, paths = generate_process_paths(paths, settings)
        if verbose : print_result()

        # Now, Perform the dcm2nii file conversion.
        if verbose : print("\nPerforming dcm2nii conversion...")
        dcm2nii(process_paths, paths, settings, verbose)
        if verbose : print("dcm2nii conversion completed!")

        # Also, perform a freesurfer file conversion.
        if verbose : print("\nPerforming FreeSurfer conversion...")
        nii2fs(process_paths, paths, settings, verbose)
        if verbose : print("FreeSurfer conversion completed!")

        if verbose : print_header("\nPREPROCESSING FINISHED")

    else:
        raise ValueError(   "Parameter 'runModules' should be a list containing only 0's and 1's. " \
                            "Please check the config file (config.json).")
    
    return paths, settings


if __name__ == "__main__":
    preprocessing(*initialization())