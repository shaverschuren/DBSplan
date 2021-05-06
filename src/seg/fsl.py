import os
import subprocess
import shutil
from tqdm import tqdm
from glob import glob
from datetime import datetime
from util.general import append_logs


def generate_fsl_paths(paths, settings):
    """
    This function generates an array of strings (paths).
    It contains all paths required for the fsl bet/fast process.
    We'll use info from dicts 'paths' and 'settings'.
    """

    fsl_paths = []

    # Create fsl log file
    if "fsl_logs" not in paths:
        paths["fsl_logs"] = os.path.join(paths["logsDir"], "fsl_logs.txt")

    # Reset logs if applicable
    if settings["resetModules"][1] == 1 and os.path.exists(paths["fsl_logs"]):
        os.remove(paths["fsl_logs"])

    # Write logs header
    write_mode = ("w" if not os.path.exists(paths["fsl_logs"]) else "a")

    now = datetime.now()
    logs_file = open(paths["fsl_logs"], write_mode)
    logs_file.write(f"==================== NEW RUN ====================\n\n"
                    f"Starting at : {now.strftime('%d/%m/%Y %H:%M:%S')}\n\n")
    logs_file.close()

    # If applicable, make fsl directory
    if "fslDir" not in paths:
        paths["fslDir"] = os.path.join(paths["tmpDataDir"], "fsl")
    if not os.path.isdir(paths["fslDir"]):
        os.mkdir(paths["fslDir"])

    # Create fsl paths struct
    if "fsl_paths" not in paths: paths["fsl_paths"] = {}

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
        path_fast_gm = path_fast_base + "_gm.nii.gz"
        path_fast_wm = path_fast_base + "_wm.nii.gz"

        # Add subject paths to {paths} and [fsl_paths]
        subject_dict = {}
        subject_dict["dir"] = os.path.join(paths["fslDir"], subject)
        subject_dict["ori"] = path_ori
        subject_dict["bet"] = path_bet
        subject_dict["fast_corr"] = path_fast_corr
        subject_dict["fast_csf"] = path_fast_csf
        subject_dict["fast_gm"] = path_fast_gm
        subject_dict["fast_wm"] = path_fast_wm

        paths["fsl_paths"][subject] = subject_dict

        fsl_paths.append([subject, path_fast_base, path_t1w, path_ori,
                          path_bet, path_fast_corr, path_fast_csf,
                          path_fast_gm, path_fast_wm])

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
    if reset and os.path.exists(path_bet): os.remove(path_bet)

    # Assemble command
    command = ["bet", path_ori, path_bet]

    # Open stream and pass command
    recon_stream = subprocess.Popen(command, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
    # Read output
    msg, error = recon_stream.communicate()
    # End stream
    recon_stream.terminate()

    # Store output in logs (timed)
    now = datetime.now()
    img_log = f"---------------- " \
              f"{now.strftime('%d/%m/%Y %H:%M:%S')}" \
              f" ----------------" \
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
    path_fast_gm = fsl_paths[7]
    path_fast_wm = fsl_paths[8]

    # If applicable, remove any files from previous runs
    if reset:
        if os.path.exists(path_fast_corr): os.remove(path_fast_corr)
        if os.path.exists(path_fast_csf): os.remove(path_fast_csf)
        if os.path.exists(path_fast_gm): os.remove(path_fast_gm)
        if os.path.exists(path_fast_wm): os.remove(path_fast_wm)

    # Assemble command
    command = ["fast",                     # main FAST call
               "--channels=1",             # Number of input channels (=1)
               "--type=1",                 # Type of input image (1=T1w)
               f"--out={path_fast_base}",  # Output base path
               "--class=3",                # Number of tissue-type classes
               "-B",                       # Flag --> Output bias-corrected img
               path_bet]                   # Input file

    # Open stream and pass command
    recon_stream = subprocess.Popen(command, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
    # Read output
    msg, error = recon_stream.communicate()
    # End stream
    recon_stream.terminate()

    # Restructure output files
    fastDir = os.path.join(paths["fsl_paths"][subject]["dir"], "fast_raw")
    if not os.path.isdir(fastDir): os.mkdir(fastDir)

    fast_output = glob(path_fast_base + "_*.nii.gz")
    for path in fast_output:
        filename = os.path.split(path)[-1]
        os.rename(path, os.path.join(fastDir, filename))

    shutil.copyfile(os.path.join(fastDir, "fast_restore.nii.gz"),
                    path_fast_corr)
    shutil.copyfile(os.path.join(fastDir, "fast_pve_0.nii.gz"),
                    path_fast_csf)
    shutil.copyfile(os.path.join(fastDir, "fast_pve_1.nii.gz"),
                    path_fast_gm)
    shutil.copyfile(os.path.join(fastDir, "fast_pve_2.nii.gz"),
                    path_fast_wm)

    # Store output in logs (timed)
    now = datetime.now()
    img_log = f"---------------- " \
              f"{now.strftime('%d/%m/%Y %H:%M:%S')}" \
              f" ----------------" \
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
        iterator = tqdm(fsl_paths, ascii=True,
                        bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}')
    else:
        iterator = fsl_paths

    # Loop over subjects in fsl_paths list
    for subject_paths in iterator:
        # Create subject directory
        subjectDir = paths["fsl_paths"][subject_paths[0]]["dir"]
        if not os.path.isdir(subjectDir): os.mkdir(subjectDir)

        # Check whether results are already there
        ok_paths = [path for path in subject_paths[2:] if os.path.exists(path)]
        output_ok = bool(len(subject_paths[2:]) == len(ok_paths))

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
                img_log = f"----------------" \
                          f"{now.strftime('%d/%m/%Y %H:%M:%S')}" \
                          f" ----------------" \
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
                raise ValueError("Parameter 'resetModules' should be a list"
                                 "containing only 0's and 1's. "
                                 "Please check the config file (config.json).")

    # If some files were skipped, write message
    if verbose and skipped_img:
        print("Some scans were skipped due to the output being complete.\n"
              "If you want to rerun this entire module, please set "
              "'resetModules'[1] to 0 in the config.json file.")

    return paths, settings
