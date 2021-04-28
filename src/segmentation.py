import sys
if "" not in sys.path : sys.path.append("")
if "src" not in sys.path : sys.path.append("src")

import os
import subprocess
import shutil
import numpy as np
import nibabel as nib
from tqdm import tqdm
from glob import glob
from datetime import datetime
from initialization import initialization
from preprocessing import preprocessing
from seg.mask_util import binarize_mask
from seg.ventricles import extract_ventricles
from util.style import print_header
from util.general import append_logs


def generate_fsl_paths(paths, settings):
    """
    This function generates an array of strings (paths). 
    It contains all paths required for the fsl bet/fast process.
    We'll use info from dicts 'paths' and 'settings'.
    """

    fsl_paths = []

    # Create fsl log file
    if "fsl_logs" not in paths : paths["fsl_logs"] = os.path.join(paths["logsDir"], "fsl_logs.txt")

    # Reset logs if applicable
    if settings["resetModules"][1] == 1 and os.path.exists(paths["fsl_logs"]) : os.remove(paths["fsl_logs"])

    # Write logs header
    write_mode = ("w" if not os.path.exists(paths["fsl_logs"]) else "a")

    now = datetime.now()
    logs_file = open(paths["fsl_logs"], write_mode)
    logs_file.write(    f"==================== NEW RUN ====================\n\n" \
                        f"Starting at : {now.strftime('%d/%m/%Y %H:%M:%S')}\n\n")
    logs_file.close()

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
        path_fast_base = os.path.join(paths["fslDir"], subject, "fast")
        path_fast_corr = path_fast_base + "_biasCorr.nii.gz"
        path_fast_csf = path_fast_base + "_csf.nii.gz"
        path_fast_m = path_fast_base + "_m.nii.gz"

        # Add subject paths to {paths} and [fsl_paths]
        subject_dict = {}
        subject_dict["dir"] = os.path.join(paths["fslDir"], subject)
        subject_dict["ori"] = path_ori
        subject_dict["bet"] = path_bet
        subject_dict["fast_corr"] = path_fast_corr
        subject_dict["fast_csf"] = path_fast_csf
        subject_dict["fast_m"] = path_fast_m

        paths["fsl_paths"][subject] = subject_dict

        fsl_paths.append([  subject, path_fast_base, path_t1w, path_ori, 
                            path_bet, path_fast_corr, path_fast_csf, path_fast_m])

    return fsl_paths, paths


def fsl_bet(fsl_paths, paths, settings, reset=True):
    """
    This function runs the FSL BET module for all relevant images, 
    as is described at https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/BET.
    This step is a.o. important for the ventricle segmentation.
    It makes use of the FSL software packages command line.
    """

    # Extract relevant info
    subject = fsl_paths[0]
    path_ori = fsl_paths[3]
    path_bet = fsl_paths[4]

    # If applicable, remove any files from previous runs
    if reset and os.path.exists(path_bet) : os.remove(path_bet)

    # Assemble command
    command = ["bet", path_ori, path_bet]

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
                f"\n\nT1w path:\t{path_ori}" \
                f"\nBET path:\t{path_bet}" \
                f"\n\n{msg.decode('utf-8')}" \
                f"\n{error.decode('utf-8')}\n\n"

    append_logs(img_log, paths["fsl_logs"])

    return paths, settings


def fsl_fast(fsl_paths, paths, settings, reset=True):
    """
    This function runs the FSL FAST module for all relevant images, 
    as is described at https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FAST.
    This step is a.o. important for the ventricle segmentation.
    It makes use of the FSL software packages command line.
    """

    # Extract relevant info
    subject = fsl_paths[0]
    path_bet = fsl_paths[4]
    path_fast_base = fsl_paths[1]
    path_fast_corr = fsl_paths[5]
    path_fast_csf = fsl_paths[6]
    path_fast_m = fsl_paths[7]

    # If applicable, remove any files from previous runs
    if reset:
        if os.path.exists(path_fast_corr) : os.remove(path_fast_corr)
        if os.path.exists(path_fast_csf) : os.remove(path_fast_csf)
        if os.path.exists(path_fast_m) : os.remove(path_fast_m)

    # Assemble command
    command = [ "fast",                     # main FAST call
                "--channels=1",             # Number of input channels (=1)
                "--type=1",                 # Type of input image (1=T1w)
                f"--out={path_fast_base}",  # Output base path
                "--class=2",                # Number of tissue-type classes (2 = CSF, other)
                "-B",                       # Flag --> Output bias-field corrected image
                path_bet]                   # Input file

    # Open stream and pass command
    recon_stream = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Read output
    msg, error = recon_stream.communicate()
    # End stream
    recon_stream.terminate()

    # Restructure output files
    fastDir = os.path.join(paths["fsl_paths"][subject]["dir"], "fast_raw")
    if not os.path.isdir(fastDir) : os.mkdir(fastDir)

    fast_output = glob(path_fast_base+"_*.nii.gz")
    for path in fast_output:
        filename = os.path.split(path)[-1]
        os.rename(path, os.path.join(fastDir, filename))
    
    shutil.copyfile(os.path.join(fastDir, "fast_restore.nii.gz"), path_fast_corr)
    shutil.copyfile(os.path.join(fastDir, "fast_pve_0.nii.gz"), path_fast_csf)
    shutil.copyfile(os.path.join(fastDir, "fast_pve_1.nii.gz"), path_fast_m)

    # Store output in logs (timed)
    now = datetime.now()
    img_log =   f"---------------- {now.strftime('%d/%m/%Y %H:%M:%S')} ----------------" \
                f"\n{command}" \
                f"\n\nBET path:\t{path_bet}" \
                f"\nFAST base:\t{path_fast_base}[...]" \
                f"\n\n{msg.decode('utf-8')}" \
                f"\n{error.decode('utf-8')}\n\n"
                
    append_logs(img_log, paths["fsl_logs"])

    return paths, settings


def process_fsl(paths, settings, verbose=True):
    """
    Main function for the fsl processing steps.
    """

    # Initialize skipped_img variable
    skipped_img = False

    # Generate fsl processing paths
    fsl_paths, paths = generate_fsl_paths(paths, settings)

    # Define iterator
    if verbose:
        iterator = tqdm(fsl_paths, ascii=True, bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}')
    else:
        iterator = fsl_paths

    # Loop over subjects in fsl_paths list
    for subject_paths in iterator:
        # Create subject directory
        subjectDir = paths["fsl_paths"][subject_paths[0]]["dir"]
        if not os.path.isdir(subjectDir) : os.mkdir(subjectDir)

        # Check whether results are already there
        output_ok = bool(len(subject_paths[2:]) == len([path for path in subject_paths[2:] if os.path.exists(path)]))

        if not output_ok:
            # Copy original T1w scan to FSL folder
            shutil.copyfile(subject_paths[2], subject_paths[3])
            # Run FSL BET
            paths, settings = fsl_bet(subject_paths, paths, settings)
            # Run FSL FAST
            paths, settings = fsl_fast(subject_paths, paths, settings)
        else:
            # Skip this subject
            if settings["resetModules"][1] == 0:
                command = "---"
                output = "Output files are already there. Skipping..."
                skipped_img = True
                # Store output in logs (timed)
                now = datetime.now()
                img_log =   f"---------------- {now.strftime('%d/%m/%Y %H:%M:%S')} ----------------" \
                            f"\n---" \
                            f"\n\nNIFTI path:\t{subject_paths[1]}" \
                            f"\nFSL path:\t{subjectDir}" \
                            + "\n\n" + output + "\n\n"
                append_logs(img_log, paths["fsl_logs"])

                continue

            # Rerun this subject
            elif settings["resetModules"][1] == 1:
                # Copy original T1w scan to FSL folder
                shutil.copyfile(subject_paths[2], subject_paths[3])
                # Run FSL BET
                paths, settings = fsl_bet(subject_paths, paths, settings)
                # Run FSL FAST
                paths, settings = fsl_fast(subject_paths, paths, settings)

            # Raise ValueError
            else:
                raise ValueError(   "Parameter 'resetModules' should be a list containing only 0's and 1's. " \
                                    "Please check the config file (config.json).")

    # If some files were skipped, write message
    if verbose and skipped_img:
        print(  "Some scans were skipped due to the output being already there.\n" \
                "If you want to rerun this entire module, please set " \
                "'resetModules'[1] to 0 in the config.json file.")
    
    return paths, settings


def seg_ventricles(paths, settings, verbose=True):
    """
    This function performs the ventricle segmentation.
    It builds upon output from FSL BET and FAST.
    """

    # If applicable, make segmentation paths and folder
    if "segDir" not in paths : paths["segDir"] = os.path.join(paths["tmpDataDir"], "segmentation")
    if "seg_paths" not in paths : paths["seg_paths"] = {}

    if not os.path.isdir(paths["segDir"]) : os.mkdir(paths["segDir"])

    # Generate processing paths (iteratively)
    seg_paths = []

    for subject, fsl_paths in paths["fsl_paths"].items():
        # Create subject dict
        subjectDir = os.path.join(paths["segDir"], subject)
        if not os.path.isdir(subjectDir) : os.mkdir(subjectDir)

        paths["seg_paths"][subject] = {"dir": subjectDir}

        # Extract fsl path
        t1w_cor_path = fsl_paths["fast_corr"]
        csf_pve_path = fsl_paths["fast_csf"]

        # Assemble segmentation paths
        csf_mask_path = os.path.join(subjectDir, "csf_mask.nii.gz")
        ventricle_mask_path = os.path.join(subjectDir, "ventricle_mask.nii.gz")

        # Add paths to {paths}
        paths["seg_paths"][subject]["csf_mask"] = csf_mask_path
        paths["seg_paths"][subject]["ventricle_mask"] = ventricle_mask_path

        # Add paths to seg_paths
        seg_paths.append([subject, t1w_cor_path, csf_pve_path, csf_mask_path, ventricle_mask_path])
    
    # Now, loop over seg_paths and perform ventricle segmentation
    # Define iterator
    if verbose:
        iterator = tqdm(seg_paths, ascii=True, bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}')
    else:
        iterator = seg_paths
    
    # Main loop
    for sub_paths in iterator:
        # TODO: Implement already-done check

        # Binarize the pve map to a 0/1 mask
        binarize_mask(sub_paths[2], sub_paths[3], treshold=0.8)
        # Generate ventricle mask
        extract_ventricles(sub_paths[1], sub_paths[3], sub_paths[4])

    return paths, settings


def segmentation(paths, settings, verbose=True):
    """
    This is the main wrapper function for the segmentation module.
    It calls on other functions to perform specific tasks.
    """

    if verbose : print_header("\n==== MODULE 2 - SEGMENTATION ====")

    # Check whether module should be run (from config file)
    if settings["runModules"][1] == 0:
        # Skip module
        _, paths = generate_fsl_paths(paths, settings)
        if verbose : print( "\nSKIPPED:\n" \
                            "'run_modules'[1] parameter == 0.\n" \
                            "Assuming all data is already segmented.\n" \
                            "Skipping segmentation process. " \
                            "Added expected paths to 'paths'.")

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
    paths, settings = segmentation(paths, settings)

    import json
    with open('paths.json', 'w') as outfile:
        json.dump(paths, outfile, sort_keys=False, indent=4)
        outfile.close()
    with open('settings.json', 'w') as outfile:
        json.dump(settings, outfile, sort_keys=False, indent=4) 
        outfile.close()