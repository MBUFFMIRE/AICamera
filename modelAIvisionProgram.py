#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading
import sys
import signal
import os
import io
from contextlib import redirect_stdout

# Import functionality from the original program
from AIvisionProgram import run_camera

class RedirectText:
    """Redirect stdout to the text widget"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = io.StringIO()
        
    def write(self, string):
        self.buffer.write(string)
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)  # Auto-scroll to the end
        self.text_widget.configure(state='disabled')
        
    def flush(self):
        pass

class AIVisionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Vision Camera")
        self.root.geometry("800x600")
        self.process = None
        self.camera_running = False
        
        # Configure the main window
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky="new")
        
        # Create header with title and start button
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=10)
        
        title_label = ttk.Label(header_frame, text="Raspberry Pi AI Vision Camera", 
                               font=("Arial", 16, "bold"))
        title_label.pack(side="left", padx=10)
        
        # AI Vision button
        self.start_button = ttk.Button(header_frame, text="AI Vision", 
                                     command=self.toggle_camera, width=15)
        self.start_button.pack(side="right", padx=10)
        
        # Status indicator
        self.status_label = ttk.Label(main_frame, text="Status: Ready", 
                                    font=("Arial", 10))
        self.status_label.pack(anchor="w", padx=10, pady=5)
        
        # Create output console
        console_frame = ttk.LabelFrame(root, text="Console Output", padding="10")
        console_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, 
                                               font=("Courier", 10))
        self.console.pack(fill="both", expand=True)
        self.console.configure(state='disabled')
        
        # Redirect stdout to the console widget
        self.stdout_redirect = RedirectText(self.console)
        
        # Bottom control frame with close button
        control_frame = ttk.Frame(root, padding="10")
        control_frame.grid(row=2, column=0, sticky="sew")
        
        self.close_button = ttk.Button(control_frame, text="Close", 
                                      command=self.close_application, width=15)
        self.close_button.pack(side="right", padx=10)
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.close_application)
    
    def toggle_camera(self):
        """Start or stop the camera based on current state"""
        if not self.camera_running:
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        """Start the AI vision camera in a separate thread"""
        if self.camera_running:
            return
            
        self.camera_running = True
        self.start_button.configure(text="Stop AI Vision")
        self.status_label.configure(text="Status: Running")
        
        # Clear console
        self.console.configure(state='normal')
        self.console.delete(1.0, tk.END)
        self.console.configure(state='disabled')
        
        # Start camera in a separate thread
        self.camera_thread = threading.Thread(target=self._run_camera_thread)
        self.camera_thread.daemon = True
        self.camera_thread.start()
    
    def _run_camera_thread(self):
        """Run the camera in a thread"""
        try:
            # Redirect stdout to capture output
            sys.stdout = self.stdout_redirect
            
            # Start the camera process
            cmd = [
                'rpicam-hello',
                '-t', '0s',
                '--post-process-file', '/usr/share/rpi-camera-assets/imx500_mobilenet_ssd.json',
                '--viewfinder-width', '1920',
                '--viewfinder-height', '1080',
                '--framerate', '30'
            ]
            
            print("Starting AI camera with object detection...")
            print(f"Command: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(cmd)
            self.process.wait()
            
            # If we get here, process has ended
            self.root.after(0, self._camera_stopped)
            
        except Exception as e:
            print(f"Error running camera: {e}")
            self.root.after(0, self._camera_stopped)
        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__
    
    def _camera_stopped(self):
        """Called when camera process stops"""
        self.camera_running = False
        self.start_button.configure(text="AI Vision")
        self.status_label.configure(text="Status: Ready")
        self.process = None
    
    def stop_camera(self):
        """Stop the camera process"""
        if self.process and self.camera_running:
            self.process.terminate()
            self.process = None
            self.camera_running = False
            self.start_button.configure(text="AI Vision")
            self.status_label.configure(text="Status: Stopped")
            print("Camera stopped by user")
    
    def close_application(self):
        """Clean up and close the application"""
        if self.camera_running:
            self.stop_camera()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AIVisionGUI(root)
    root.mainloop()