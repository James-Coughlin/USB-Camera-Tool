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
        description='Take and store USB images',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('directory',
                        metavar='dir',
                        help='Storage directory for output photos')

    parser.add_argument('-i',
                        '--interval',
                        metavar='[int]',
                        help='Interval in seconds',
                        type=int,
                        default=5)

    parser.add_argument('-d',
                        '--duration',
                        metavar='[int]',
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
                        metavar='FPS',
                        help='Frames per second for the timelapse',
                        type=int,
                        default=60)

    args = parser.parse_args()

    return Args(args.directory, args.interval, args.duration, args.debug, args.videoMode, args.videoFrames)

# --------------------------------------------------
def main() -> None:
    """ Main flow of the tool"""

    # Get arguments from command line
    args = get_args()
    directory = args.directory
    duration = args.duration
    interval = args.interval

    # Find the number of Cameras attached
    cameras = usb.core.find(find_all=True,idVendor=0x32e4)
    num_Cams = len(list(cameras))

    # Create a main directory and sub directories for each camera
    if os.path.isdir(directory):
        print("Directory already exists: Overwrite(Y/N)")
        if input() == "Y":
            pass
        else:
            exit()
    else:
        os.mkdir(directory)
        for i in range(num_Cams):
            os.mkdir(directory + "/camera_" + str(i + 1))

    # Function to open picture taking threads
    openCams(directory, num_Cams, duration, interval)

    # Time lapse the image sets
    if args.videoMode:
        print("Condensing images to video")
        for camera in os.listdir(directory):
            img2video(directory, camera, args.videoFrames)

# --------------------------------------------------
def openCams(directory, num_Cams, duration, interval):
    """ wrapper for capture loop """
    print("Starting to take pictures")
    threads = []

    # First Camera
    img_dir_1 = directory + "/camera_1"
    cam1 = Thread(target=captureLoop, args=(img_dir_1, duration,interval, 0))
    cam1.start()
    threads.append(cam1)

    # Second Camera
    if num_Cams > 1:
        img_dir_2 = directory + "/camera_2"
        cam2 = Thread(target=captureLoop, args=(img_dir_2, duration,interval, 2))
        cam2.start()
        threads.append(cam2)

    # Third Camera
    if num_Cams > 2:
        img_dir_3 = directory + "/camera_3"
        cam3 = Thread(target=captureLoop, args=(img_dir_3, duration,interval, 4))
        cam3.start()
        threads.append(cam3)

    # Fourth Camera
    if num_Cams > 3:
        img_dir_4 = directory + "/camera_4"
        cam4 = Thread(target=captureLoop, args=(img_dir_4, duration,interval, 6))
        cam4.start()
        threads.append(cam4)

    # Fifth Camera
    if num_Cams > 4:
        img_dir_5 = directory + "/camera_5"
        cam5 = Thread(target=captureLoop, args=(img_dir_5, duration,interval, 8))
        cam5.start()
        threads.append(cam5)

    # Sixth Camera
    if num_Cams > 5:
        img_dir_6 = directory + "/camera_6"
        cam6 = Thread(target=captureLoop, args=(img_dir_6, duration,interval, 10))
        cam6.start()
        threads.append(cam6)

    # Join threads
    for i in threads:
        i.join()
    return print("All Pictures Taken")
# --------------------------------------------------
def captureLoop(directory, duration, interval, camera_index):
    ''' Defines the loop to take pictures '''

    images = int(duration/interval)
    pic_time = [x * interval for x in list(range(images))]
    count = 0
    img_num = 0

    cap = cv2.VideoCapture(camera_index + cv2.CAP_V4L2)
    while True:
        ret, frame = cap.read()

        if count == pic_time[img_num]:
           _, still = cap.read()
           file_path = directory + "/capture_" + str(img_num) + ".png"
           cv2.imwrite(file_path, still)

           if img_num == (images - 1):
               cap.release()
               cv2.destroyAllWindows()
               return

           img_num += 1

        # Wait 1 second and check conditions again
        time.sleep(1)
        count += 1
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

    out.release()
    cv2.destroyAllWindows()
    os.chdir('../..')
    print("The output video is {}".format(output))

# --------------------------------------------------
if __name__ == '__main__':
    main()
