#!/usr/bin/env python3

import subprocess
import time
import signal
import sys
import argparse
from pyzbar.pyzbar import decode
import webbrowser
import threading
import os
import tempfile
import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# Function to open URLs without prompts
def force_open_url(url):
    """Open URL without any prompts by using direct browser commands"""
    try:
        # First try Chromium in app mode (no cookie prompts)
        subprocess.Popen([
            "chromium-browser", 
            "--app=" + url,  # App mode bypasses cookie prompts
            "--start-maximized"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        try:
            # Try Firefox with preferences set to auto-accept cookies
            subprocess.Popen([
                "firefox",
                "-new-tab",
                url
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            # Last resort: use xdg-open and auto-answer Y to all prompts
            try:
                process = subprocess.Popen(
                    ["xdg-open", url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return True
            except:
                # Final fallback
                return webbrowser.open(url)

class QRCodeReaderGUI:
    def __init__(self, width=1280, height=720, framerate=5):
        self.width = width
        self.height = height
        self.framerate = framerate  # Frames per second to capture
        self.running = False
        self.last_url = None
        self.last_detection_time = 0
        self.cooldown_period = 5  # Seconds between opening the same URL
        
        # Create temporary directory for images
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file = os.path.join(self.temp_dir.name, "frame.jpg")
        
        # Setup GUI
        self.root = tk.Tk()
        self.root.title("QR Code Scanner")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Configure the window size
        display_width = min(width, 800)  # Limit max width for display
        display_height = int(display_width * height / width)  # Maintain aspect ratio
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Video frame
        self.video_frame = ttk.Frame(main_frame, width=display_width, height=display_height)
        self.video_frame.pack(pady=5)
        
        # Video label
        self.video_label = ttk.Label(self.video_frame)
        self.video_label.pack()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Scanner ready. Waiting for QR codes...")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=5)
        
        # Last URL frame
        url_frame = ttk.LabelFrame(main_frame, text="Last Detected URL")
        url_frame.pack(fill=tk.X, pady=5)
        
        self.url_var = tk.StringVar()
        self.url_var.set("None")
        url_label = ttk.Label(url_frame, textvariable=self.url_var, 
                             wraplength=display_width-20)
        url_label.pack(fill=tk.X, padx=5, pady=5)
        
        # Add Open URL button
        self.open_button = ttk.Button(url_frame, text="Open URL in Browser", 
                                     command=self._open_current_url)
        self.open_button.pack(pady=5)
        self.open_button.config(state=tk.DISABLED)  # Initially disabled
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        quit_button = ttk.Button(control_frame, text="Quit", command=self.on_close)
        quit_button.pack(side=tk.RIGHT, padx=5)
        
        # Set window size
        self.root.geometry(f"{display_width}x{display_height+180}")
    
    def _open_current_url(self):
        """Open the current URL in the web browser"""
        if self.last_url and self.last_url.startswith(('http://', 'https://')):
            self.status_var.set(f"Opening URL: {self.last_url}")
            force_open_url(self.last_url)
        else:
            self.status_var.set("No valid URL to open")
        
    def start(self):
        """Start the camera and QR code detection"""
        self.status_var.set("Starting camera...")
        self.root.update()
        
        self.running = True
        
        # Start the capture and processing in separate threads
        self.capture_thread = threading.Thread(target=self._capture_frames)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        # Start the UI update loop
        self._update_frame()
        
        # Start the Tkinter main loop
        self.root.mainloop()
        
    def _capture_frames(self):
        """Continuously capture frames and process them for QR codes"""
        try:
            while self.running:
                try:
                    # Capture frame using libcamera-still
                    cmd = [
                        "libcamera-still",
                        "--width", str(self.width),
                        "--height", str(self.height),
                        "--output", self.temp_file,
                        "--immediate",
                        "--nopreview",
                        "--timeout", "1"
                    ]
                    
                    # Run the command
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Process frame for QR codes
                    self._process_current_frame()
                    
                    # Delay between captures based on framerate
                    time.sleep(1.0 / self.framerate)
                    
                except subprocess.CalledProcessError as e:
                    self.status_var.set(f"Error capturing image: {e}")
                    time.sleep(1)
                    
        except Exception as e:
            self.status_var.set(f"Capture error: {e}")
    
    def _process_current_frame(self):
        """Process the current frame to detect QR codes"""
        try:
            # Check if the image file exists
            if not os.path.exists(self.temp_file):
                return
            
            # Read the image
            frame = cv2.imread(self.temp_file)
            
            if frame is None:
                return
            
            # Process the frame to detect QR codes
            qr_codes = decode(frame)
            
            for qr in qr_codes:
                # Get the data from the QR code
                data = qr.data.decode('utf-8')
                
                # Check if the data is a URL
                if data.startswith(('http://', 'https://')):
                    current_time = time.time()
                    
                    # Only process if it's a new URL or enough time has passed
                    if (data != self.last_url or 
                        (current_time - self.last_detection_time) > self.cooldown_period):
                        
                        self.status_var.set(f"QR Code detected! Opening: {data}")
                        self.url_var.set(data)
                        self.last_url = data
                        self.last_detection_time = current_time
                        
                        # Enable the open URL button
                        self.root.after(0, lambda: self.open_button.config(state=tk.NORMAL))
                        
                        # Open URL directly without confirmation
                        force_open_url(data)
                else:
                    self.status_var.set(f"Detected QR code with non-URL data: {data}")
                    self.url_var.set(f"Non-URL data: {data}")
                    
                    # Disable the open URL button for non-URLs
                    self.root.after(0, lambda: self.open_button.config(state=tk.DISABLED))
                    
        except Exception as e:
            self.status_var.set(f"Error processing frame: {e}")
    
    def _update_frame(self):
        """Update the UI with the latest frame"""
        if not self.running:
            return
            
        try:
            if os.path.exists(self.temp_file):
                # Load the image with PIL
                pil_image = Image.open(self.temp_file)
                
                # Resize for display
                display_width = min(self.width, 800)
                display_height = int(display_width * self.height / self.width)
                pil_image = pil_image.resize((display_width, display_height), Image.LANCZOS)
                
                # Convert to Tkinter format
                tk_image = ImageTk.PhotoImage(pil_image)
                
                # Update the label
                self.video_label.config(image=tk_image)
                self.video_label.image = tk_image  # Keep a reference to prevent garbage collection
                
        except Exception as e:
            self.status_var.set(f"Error updating frame: {e}")
            
        # Schedule the next update
        self.root.after(50, self._update_frame)  # Update every 50ms (20 FPS UI)
    
    def on_close(self):
        """Handle window close event"""
        self.running = False
        time.sleep(0.5)  # Give threads time to clean up
        
        # Clean up the temporary directory
        if hasattr(self, 'temp_dir'):
            self.temp_dir.cleanup()
            
        self.root.destroy()
        sys.exit(0)

def main():
    """Main function to run the QR code reader GUI"""
    parser = argparse.ArgumentParser(description='QR Code Reader with GUI')
    parser.add_argument('-w', '--width', type=int, default=1280,
                        help='Camera width in pixels')
    parser.add_argument('-H', '--height', type=int, default=720,
                        help='Camera height in pixels')
    parser.add_argument('-f', '--framerate', type=int, default=5,
                        help='Frames per second (1-10 recommended)')
    
    args = parser.parse_args()
    
    # Limit framerate to a reasonable range
    framerate = max(1, min(10, args.framerate))
    
    # Create and start the QR code reader GUI
    app = QRCodeReaderGUI(
        width=args.width,
        height=args.height,
        framerate=framerate
    )
    
    # Set up signal handler for graceful exit
    def signal_handler(sig, frame):
        app.on_close()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        app.start()
    except Exception as e:
        print(f"Error: {e}")
        app.on_close()

if __name__ == "__main__":
    main()