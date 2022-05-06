#!/usr/bin/env python3
"""
Author : jim <jcoughl3@binghamton.edu>
Date   : 2022-05-03
Purpose: USB camera tool for use alongside rocker platfrom
Version: v.05
"""

import argparse
from typing import NamedTuple
import os, time, shutil
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

    # Find the number of Cameras attached
    num_Cams = len(list(usb.core.find(find_all=True,idVendor=0x32e4)))

    # Create a main directory and sub directories for each camera
    if os.path.isdir(directory):
        print("Directory already exists: Exiting...")
        exit()
    else:
        os.mkdir(directory)
        for i in range(num_Cams):
            os.mkdir(f"{directory}/camera_{str(i +1)}")

    # Function to open picture taking threads
    openCams(directory, num_Cams, duration, interval)

    # Time lapse the image sets
    if args.videoMode:
        print("Condensing images to video")
        for camera in os.listdir(directory):
            img2video(directory, camera, args.videoFrames)

# --------------------------------------------------
def openCams(directory, num_Cams, duration, interval):
    """ Wrapper for capture loop """
    print("Starting to take pictures")
    threads = []

    # Opens a thread for each camera with a target function of captureLoop
    for i in range(num_Cams):
        t = Thread(target=captureLoop, args=(f"{directory}/camera_{i+1}", duration, interval, (i * 2)))
        t.start()
        threads.append(t)

    # Join threads
    for i in threads:
        i.join()
    return print("All Pictures Taken")

# --------------------------------------------------
def captureLoop(directory, duration, interval, camera_index):
    """ Picture taking loop """

    # Define the number of pictures to take and initialize which image is being taken
    images = int(duration/interval)
    img_num = 0

    # Opens the VideoCapture object
    cap = cv2.VideoCapture(camera_index + cv2.CAP_V4L2)

    # Save an image and wait for the interval before saving again
    for image in range(images):
        _, frame = cap.read()
        file_path = f"{directory}/capture_{img_num}.png"

        cv2.imwrite(file_path, frame)

        img_num += 1
        time.sleep(interval)

    # Close the VideoCapture object
    cap.release()
    cv2.destroyAllWindows()
    return

# --------------------------------------------------
def img2video(directory, camera, fps):

    path = os.path.join(directory, camera)
    os.chdir(path)

    images = []
    for f in os.listdir():
        if f.endswith('.png'):
            images.append(f)

    images.sort(key=lambda x: os.path.getmtime(x))


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
    print(f"The output video saved as {output}")
    return

# --------------------------------------------------
if __name__ == '__main__':
    main()
