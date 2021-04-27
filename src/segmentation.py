import sys
if "" not in sys.path : sys.path.append("")
if "src" not in sys.path : sys.path.append("src")

import os
import subprocess
import shutil
from tqdm import tqdm
from datetime import datetime
from initialization import initialization
from preprocessing import preprocessing
from util.style import print_header


def generate_fsl_paths(paths, settings):
    """
    This function generates an array of strings (paths). 
    It contains all paths required for the fsl bet/fast process.
    We'll use info from dicts 'paths' and 'settings'.
    """

    fsl_paths = []

    # If applicable, make fsl directory
    if "fslDir" not in paths : paths["fslDir"] = os.path.join(paths["tmpDataDir"], "fsl") 
    if not os.path.isdir(paths["fslDir"]) : os.mkdir(paths["fslDir"])

    # Create fsl paths struct
    if "fsl_paths" not in paths : paths["fsl_paths"] = {}

    # Loop over subjects
    for subject, scans in paths["nii_paths"].items():
        # Retrieve T1w nifti path
        path_t1w = scans["MRI_T1W"]
        
        # Create FSL processing paths
        path_ori = os.path.join(paths["fslDir"], subject, "T1w_ori.nii.gz")
        path_bet = os.path.join(paths["fslDir"], subject, "T1w_bet.nii.gz")
        path_fast_csf = os.path.join(paths["fslDir"], subject, "csf_mask.nii.gz")
        path_fast_wm = os.path.join(paths["fslDir"], subject, "wm_mask.nii.gz")
        path_fast_gm = os.path.join(paths["fslDir"], subject, "gm_mask.nii.gz")

        # Add subject paths to {paths} and [fsl_paths]
        paths["fsl_paths"][subject] = os.path.join(paths["fslDir"], subject)
        fsl_paths.append([path_t1w, path_ori, path_bet, path_fast_csf, path_fast_wm, path_fast_gm])

    return fsl_paths, paths


def fsl_fast(paths, settings, verbose=True):
    """
    This function runs the FSL FAST module for all relevant images, 
    as is described at https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FAST.
    This step is a.o. important for the ventricle segmentation.
    It makes use of the FSL software packages command line.
    """

    # Initialize logs string and skipped_img variable
    log_str = ""
    skipped_img = False

    # Remove irrelevant scans from list
    process_paths = []
    raise UserWarning("Still working on this function!!")

    # Define iterator
    if verbose:
        iterator = tqdm(range(len(process_paths)), ascii=True, bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}')
    else:
        iterator = range(len(process_paths))

    # # Loop over the dcm,nii path pairs and perform the conversion.
    # for img_i in iterator:
    #     # Extract paths from array
    #     _, nii_path, fs_path = process_paths[img_i]

    #     if os.path.exists(fs_path):
    #         # If output folder already exists, skip this image
    #         if settings["resetModules"][0] == 0:
    #             command = "---"
    #             output = "Output files are already there. Skipping..."
    #             skipped_img = True
    #             # Store output in logs (timed)
    #             now = datetime.now()
    #             img_log =   f"---------------- {now.strftime('%d/%m/%Y %H:%M:%S')} ----------------" \
    #                         f"\n{command}" \
    #                         f"\n\nNIFTI path:\t\t{nii_path}" \
    #                         f"\nFreeSurfer path:\t{fs_path}" \
    #                         + "\n\n" + output + "\n\n"
    #             log_str = log_str + img_log
    #             continue

    #         # If output freesurfer folder already exists, remove it.
    #         elif settings["resetModules"][0] == 1:
    #             shutil.rmtree(fs_path)

    #         # Other: Raise error
    #         else:
    #             raise ValueError(   "Parameter 'resetModules' should be a list containing only 0's and 1's. " \
    #                                 "Please check the config file (config.json).")

    #     # Assemble command
    #     command = [ "recon-all", 
    #                 "-subjid", os.path.split(fs_path)[-1], 
    #                 "-i", nii_path, 
    #                 "-sd", paths["fsDir"],
    #                 "-3T",
    #                 "-autorecon1"]

    #     # Open stream and pass command
    #     recon_stream = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #     # Read output
    #     msg, error = recon_stream.communicate()
    #     # End stream
    #     recon_stream.terminate()

    #     # Store output in logs (timed)
    #     now = datetime.now()
    #     img_log =   f"---------------- {now.strftime('%d/%m/%Y %H:%M:%S')} ----------------" \
    #                 f"\n{command}" \
    #                 f"\n\nNIFTI path:\t\t{nii_path}" \
    #                 f"\nFreeSurfer path:\t{fs_path}" \
    #                 f"\n\n{msg.decode('utf-8')}" \
    #                 f"\n{error.decode('utf-8')}\n\n"

    #     log_str = log_str + img_log

    # # Write logs to text file
    # logs_path = os.path.join(paths["logsDir"], "nii2freesurfer_logs.txt")
    # logs_file = open(logs_path, "w")
    # logs_file.write(log_str)
    # logs_file.close()

    # If some files were skipped, write message
    if verbose and skipped_img:
        print(  "Some scans were skipped due to the output being already there.\n" \
                "If you want to rerun this entire module, please set " \
                "'resetModules'[1] to 0 in the config.json file.")
    
    return


def process_fsl(paths, settings, verbose=True):
    """
    Main function for the fsl processing steps.
    """

    # Generate fsl processing paths
    fsl_paths, paths = generate_fsl_paths(paths, settings)

    for subject_paths in fsl_paths:
        # Run FSL BET

        # Run FSL FAST
        
        continue

    return paths, settings


def seg_ventricles(paths, settings, verbose=True):

    return


def segmentation(paths, settings, verbose=True):
    """
    This is the main wrapper function for the segmentation module.
    It calls on other functions to perform specific tasks.
    """

    if verbose : print_header("\n==== MODULE 2 - SEGMENTATION ====")

    # Check whether module should be run (from config file)
    if settings["runModules"][1] == 0:
        # Skip module
        if verbose : print( "\nSKIPPED:\n" \
                            "'run_modules'[1] parameter == 0.\n" \
                            "Assuming all data is already segmented.\n" \
                            "Skipping segmentation process. " \
                            "Added expected nifti paths to 'paths'.")

    elif settings["runModules"][1] == 1:   
        # Run module
        

        if verbose : print("\nRunning FSL BET/FAST...")
        paths, settings = process_fsl(paths, settings, verbose)
        if verbose : print("FSL BET/FAST completed!")

        if verbose : print("\nPerforming ventricle segmentation...")
        seg_ventricles(paths, settings, verbose)
        if verbose : print("Ventricle segmentation completed!")

        if verbose : print_header("\nSEGMENTATION FINISHED")

    else:
        raise ValueError(   "parameter run_modules should be a list containing only 0's and 1's. " \
                            "Please check the config file (config.json).")
    
    return paths, settings


if __name__ == "__main__":
    paths, settings = preprocessing(*initialization())
    segmentation(paths, settings)