#!/usr/bin/env python3
import subprocess
import argparse
import time
import signal
import sys

class IMX500Camera:
    def __init__(self, 
                 model_file="/usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json",
                 width=1920, 
                 height=1080, 
                 framerate=30):
        """
        Initialize the IMX500 camera with the specified parameters.
        
        Args:
            model_file: Path to the post-processing model file
            width: Viewfinder width in pixels
            height: Viewfinder height in pixels
            framerate: Camera framerate
        """
        self.model_file = model_file
        self.width = width
        self.height = height
        self.framerate = framerate
        self.process = None
        
    def start(self, timeout="0s"):
        """
        Start the camera with the specified timeout.
        
        Args:
            timeout: How long to run the camera (e.g., "0s" for indefinite)
        """
        cmd = [
            "rpicam-hello",
            "-t", timeout,
            "--post-process-file", self.model_file,
            "--viewfinder-width", str(self.width),
            "--viewfinder-height", str(self.height),
            "--framerate", str(self.framerate)
        ]
        
        print(f"Starting camera with command: {' '.join(cmd)}")
        
        # Start the process
        self.process = subprocess.Popen(cmd)
        
    def stop(self):
        """Stop the camera process if it's running."""
        if self.process:
            print("Stopping camera...")
            self.process.terminate()
            self.process.wait()
            self.process = None
            print("Camera stopped.")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("Ctrl+C detected, shutting down...")
    if 'camera' in globals():
        camera.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handling for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Control the IMX500 camera with MobileNet SSD model")
    parser.add_argument("--model", default="/usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json",
                       help="Path to the post-processing model file")
    parser.add_argument("--width", type=int, default=1920, help="Viewfinder width")
    parser.add_argument("--height", type=int, default=1080, help="Viewfinder height")
    parser.add_argument("--framerate", type=int, default=30, help="Camera framerate")
    parser.add_argument("--timeout", default="0s", help="Camera runtime (0s for indefinite)")
    
    args = parser.parse_args()
    
    # Create and start the camera
    camera = IMX500Camera(
        model_file=args.model,
        width=args.width,
        height=args.height,
        framerate=args.framerate
    )
    
    try:
        camera.start(timeout=args.timeout)
        print("Camera running. Press Ctrl+C to stop.")
        
        # Keep the script running until Ctrl+C
        while camera.process.poll() is None:
            time.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        camera.stop()