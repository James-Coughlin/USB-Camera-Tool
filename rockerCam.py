#!/usr/bin/env python3
"""
Author : jim <jcoughl3@binghamton.edu>
Date   : 2022-05-03
Purpose: USB camera tool for use alongside rocker platfrom
Version: v.05
"""

import argparse
from typing import NamedTuple
import os, time, shutil, logging
import cv2 #Needs pip
import imutils #Needs pip
import usb.core #Needs pip
from threading import Thread



class Args(NamedTuple):
    """ Command-line arguments """
    directory: dir
    interval: int
    duration: int
    debug: bool
    videoMode: bool
    videoFrames: int

# --------------------------------------------------
def get_args() -> Args:
    """ Get command-line arguments """

    parser = argparse.ArgumentParser(
        description='Microscope camera tool to be used alongside Rocker Platform',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('directory',
                        metavar='Folder',
                        help='Main directory to store captured images')

    parser.add_argument('-i',
                        '--interval',
                        help='Interval in seconds',
                        type=int,
                        default=5)

    parser.add_argument('-d',
                        '--duration',
                        help='Duration of time in seconds to take pictures',
                        type=int,
                        default=15)

    parser.add_argument('--debug',
                        action='store_true',
                        help='Runs the tools in debug mode')

    parser.add_argument('-vm',
                        '--videoMode',
                        action='store_true',
                        help='Creates a timelapse from the captures')

    parser.add_argument('-vf',
                        '--videoFrames',
                        help='Frames per second for the timelapse',
                        type=int,
                        default=60)

    args = parser.parse_args()

    if args.duration == 0 or args.interval == 0:
        raise Exception('Zeroes not allowed for duration or interval')

    if os.path.isdir(args.directory):
        print("Directory exists: Overwrite (y/n)")
        shutil.rmtree(args.directory) if input() == 'y' else exit()

    return Args(args.directory,
                args.interval,
                args.duration,
                args.debug,
                args.videoMode,
                args.videoFrames)

# --------------------------------------------------
def main() -> None:
    """ Main flow of the tool"""

    # Get arguments from command line
    args = get_args()
    directory = args.directory
    duration = args.duration
    interval = args.interval

    # loggin
    if args.debug:
        global logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)s:%(funcName)s:%(threadName)s:%(message)s")
        file_handler = logging.FileHandler('rockerLogs.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Find the number of Cameras attached
    num_Cams = len(list(usb.core.find(find_all=True,idVendor=0x32e4)))
    if num_Cams == 0:
        raise Exception('Zero cameras detected')

    # Create a main directory and sub directories for each camera
    os.mkdir(directory)
    for i in range(num_Cams):
        os.mkdir(f"{directory}/camera_{str(i +1)}")
    logger.debug(f"Created {directory} in {os.getcwd()} and created {num_Cams} camera folders")

    # Function to open picture taking threads
    openCams(directory, num_Cams, duration, interval)
    print("All pictures taken")

    # Time lapse the image sets
    if args.videoMode:
        for camera in os.listdir(directory):
            img2video(directory, camera, args.videoFrames)
        print("Output video saved")

# --------------------------------------------------
def openCams(directory, num_Cams, duration, interval):
    """ Wrapper for capture loop """
    print("Starting to take pictures...")
    threads = []

    # Opens a thread for each camera with a target function of captureLoop
    for i in range(num_Cams):
        t = Thread(target=captureLoop, args=(f"{directory}/camera_{i+1}", duration, interval, (i * 2)))
        logger.debug(f"Started thread for camera {i + 1}")
        t.start()
        threads.append(t)

    # Join threads
    for i in threads:
        i.join()
    logger.debug(f"Total of {(duration // interval) * num_Cams} pictures taken")
    return

# --------------------------------------------------
def captureLoop(directory, duration, interval, camera_index):
    ''' Defines the loop to take pictures '''

    # Define the number of pictures needed and find the times where each picture should be taken
    images = int(duration/interval)
    pic_time = [x * interval for x in list(range(images + 1))]

    # Intialize the count and img_num for saving
    count = 0
    img_num = 0

    # Open the VideoCapture object
    cap = cv2.VideoCapture(camera_index + cv2.CAP_V4L2)
    logger.debug(f"VideoCapture object opened as {cap}")

    while img_num <= images:
        _, frame = cap.read() # Important to continously update to get correct interval
        # Checks if a picture needs to taken
        if count == pic_time[img_num]:
            _, frame = cap.read()
            file_path = f"{directory}/capture_{img_num}.png"
            cv2.imwrite(file_path, frame)
            img_num += 1

        # Wait 1 second and check conditions again
        time.sleep(1)
        count += 1

    # Delete zeroth picture because its typically taken before autofocus
    os.remove(f"{directory}/capture_0.png")

    # Release VideoCapture object
    cap.release()
    cv2.destroyAllWindows()
    return

# --------------------------------------------------
def img2video(directory, camera, fps):

    path = os.path.join(directory, camera)
    os.chdir(path)

    # Find and sort images into a list
    images = []
    for f in os.listdir():
        if f.endswith('.png'):
            images.append(f)

    images.sort(key=lambda x: os.path.getmtime(x))
    logger.debug(f"Found {len(images)} images to be turned into time lapse from {camera}")

    # Determine the width and height from the first image
    frame = cv2.imread(images[0])
    height, width, channels = frame.shape

    # Define the codec and create a VideoWriter object
    output = camera + "_video.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output, fourcc, fps, (width, height))

    # Make the video
    for image in images:
        frame = cv2.imread(image)
        out.write(frame)

    # Release the VideoWriter object and return
    out.release()
    cv2.destroyAllWindows()
    os.chdir('../..')
    logger.debug(f"The output video saved as {output}")
    return

# --------------------------------------------------
if __name__ == '__main__':
    main()
