#!/usr/bin/env python3

import subprocess
import time
import signal
import sys
import argparse

def run_camera_with_pose_detection(duration=0, width=1920, height=1080, framerate=30, 
                                  model_path="/usr/share/rpi-camera-assets/imx500_posenet.json"):
    """
    Run the RPi camera with pose detection using the specified parameters.
    
    Args:
        duration (int): Duration in seconds (0 for continuous)
        width (int): Viewfinder width in pixels
        height (int): Viewfinder height in pixels
        framerate (int): Camera framerate
        model_path (str): Path to the post-processing model file
    """
    # Construct the command
    cmd = [
        "rpicam-hello",
        "-t", f"{duration}s",
        "--post-process-file", model_path,
        "--viewfinder-width", str(width),
        "--viewfinder-height", str(height),
        "--framerate", str(framerate)
    ]
    
    print(f"Starting camera with pose detection...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Run the command as a subprocess
        process = subprocess.Popen(cmd)
        
        # Set up signal handler for graceful exit
        def signal_handler(sig, frame):
            print("\nStopping camera...")
            process.terminate()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Wait for the process to complete
        process.wait()
        
    except Exception as e:
        print(f"Error running camera: {e}")
        return False
    
    return True

def main():
    """Main function to parse arguments and run the camera."""
    parser = argparse.ArgumentParser(description='Run RPi camera with pose detection')
    parser.add_argument('-t', '--time', type=int, default=0,
                        help='Duration in seconds (0 for continuous)')
    parser.add_argument('-w', '--width', type=int, default=1920,
                        help='Viewfinder width in pixels')
    # Changed -h to -H for height to avoid conflict with help
    parser.add_argument('-H', '--height', type=int, default=1080,
                        help='Viewfinder height in pixels')
    parser.add_argument('-f', '--framerate', type=int, default=30,
                        help='Camera framerate')
    parser.add_argument('-m', '--model', type=str, 
                        default="/usr/share/rpi-camera-assets/imx500_posenet.json",
                        help='Path to the post-processing model file')
    
    args = parser.parse_args()
    
    # Run the camera with the specified parameters
    run_camera_with_pose_detection(
        duration=args.time,
        width=args.width,
        height=args.height,
        framerate=args.framerate,
        model_path=args.model
    )

if __name__ == "__main__":
    main()