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
        self.qr_reader_process = None
        self.model_ai_process = None
        
        # Configure the main window
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky="new")
        
        # Create header with title and buttons
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=10)
        
        title_label = ttk.Label(header_frame, text="Raspberry Pi AI Vision Camera", 
                               font=("Arial", 16, "bold"))
        title_label.pack(side="left", padx=10)
        
        # Button frame for multiple buttons
        button_frame = ttk.Frame(header_frame)
        button_frame.pack(side="right")
        
        # Model AI Vision button
        self.model_ai_button = ttk.Button(button_frame, text="Model AI", 
                                        command=self.toggle_model_ai, width=15)
        self.model_ai_button.pack(side="left", padx=5)
        
        # QR Reader button
        self.qr_button = ttk.Button(button_frame, text="QR Reader", 
                                   command=self.toggle_qr_reader, width=15)
        self.qr_button.pack(side="left", padx=5)
        
        # AI Vision button
        self.start_button = ttk.Button(button_frame, text="AI Vision", 
                                     command=self.toggle_camera, width=15)
        self.start_button.pack(side="left", padx=5)
        
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
    
    def toggle_model_ai(self):
        """Toggle Model AI Vision on/off"""
        if self.model_ai_process is None:
            self.start_model_ai()
        else:
            self.stop_model_ai()
    
    def start_model_ai(self):
        """Start the Model AI Vision application"""
        if self.model_ai_process is not None:
            return
            
        # Stop other processes if they're running
        if self.camera_running:
            self.stop_camera()
        
        if self.qr_reader_process:
            self.stop_qr_reader()
        
        # Update status
        self.status_label.configure(text="Status: Starting Model AI Vision...")
        self.model_ai_button.configure(text="Stop Model AI")
        
        # Clear console
        self.console.configure(state='normal')
        self.console.delete(1.0, tk.END)
        self.console.configure(state='disabled')
        
        # Path to Model AI Vision
        model_ai_path = "/home/mbuffmire/Documents/AICamera/modelAIvisionProgram.py"
        
        # Start Model AI Vision in a new process
        try:
            print("Starting Model AI Vision application...")
            
            # Get python interpreter path (use same as current process)
            python_path = sys.executable
            
            # Start Model AI Vision process
            self.model_ai_process = subprocess.Popen(
                [python_path, model_ai_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Start thread to read output
            threading.Thread(target=self._read_model_ai_output, daemon=True).start()
            
            print("Model AI Vision started successfully")
            self.status_label.configure(text="Status: Model AI Vision Running")
            
        except Exception as e:
            print(f"Error starting Model AI Vision: {e}")
            self.status_label.configure(text=f"Status: Error - {str(e)}")
            self.model_ai_button.configure(text="Model AI")
            self.model_ai_process = None
    
    def _read_model_ai_output(self):
        """Read and display output from Model AI Vision process"""
        while self.model_ai_process:
            try:
                # Read a line from the process output
                line = self.model_ai_process.stdout.readline()
                if not line and self.model_ai_process.poll() is not None:
                    break
                
                if line:
                    print(f"Model AI: {line.strip()}")
            except:
                break
        
        # Check if process has ended
        if self.model_ai_process and self.model_ai_process.poll() is not None:
            self.root.after(0, self._model_ai_stopped)
    
    def _model_ai_stopped(self):
        """Called when Model AI Vision process stops"""
        returncode = self.model_ai_process.poll() if self.model_ai_process else None
        self.model_ai_process = None
        self.model_ai_button.configure(text="Model AI")
        self.status_label.configure(text=f"Status: Model AI Vision Exited (code: {returncode})")
        print(f"Model AI Vision process ended with code: {returncode}")
    
    def stop_model_ai(self):
        """Stop the Model AI Vision process"""
        if self.model_ai_process:
            print("Stopping Model AI Vision...")
            self.model_ai_process.terminate()
            # Wait briefly for process to terminate
            try:
                self.model_ai_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.model_ai_process.kill()
            
            self.model_ai_process = None
            self.model_ai_button.configure(text="Model AI")
            self.status_label.configure(text="Status: Model AI Vision Stopped")
            
    def toggle_qr_reader(self):
        """Toggle QR Reader on/off"""
        if self.qr_reader_process is None:
            self.start_qr_reader()
        else:
            self.stop_qr_reader()
    
    def start_qr_reader(self):
        """Start the QR Reader application"""
        if self.qr_reader_process is not None:
            return
            
        # Stop other processes if they're running
        if self.camera_running:
            self.stop_camera()
        
        if self.model_ai_process:
            self.stop_model_ai()
        
        # Update status
        self.status_label.configure(text="Status: Starting QR Reader...")
        self.qr_button.configure(text="Stop QR Reader")
        
        # Clear console
        self.console.configure(state='normal')
        self.console.delete(1.0, tk.END)
        self.console.configure(state='disabled')
        
        # Path to QR Reader
        qr_reader_path = "/home/mbuffmire/Documents/AICamera/QRReader.py"
        
        # Start QR Reader in a new process
        try:
            print("Starting QR Reader application...")
            
            # Get python interpreter path (use same as current process)
            python_path = sys.executable
            
            # Start QR Reader process
            self.qr_reader_process = subprocess.Popen(
                [python_path, qr_reader_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Start thread to read output
            threading.Thread(target=self._read_qr_reader_output, daemon=True).start()
            
            print("QR Reader started successfully")
            self.status_label.configure(text="Status: QR Reader Running")
            
        except Exception as e:
            print(f"Error starting QR Reader: {e}")
            self.status_label.configure(text=f"Status: Error - {str(e)}")
            self.qr_button.configure(text="QR Reader")
            self.qr_reader_process = None
    
    def _read_qr_reader_output(self):
        """Read and display output from QR Reader process"""
        while self.qr_reader_process:
            try:
                # Read a line from the process output
                line = self.qr_reader_process.stdout.readline()
                if not line and self.qr_reader_process.poll() is not None:
                    break
                
                if line:
                    print(f"QR Reader: {line.strip()}")
            except:
                break
        
        # Check if process has ended
        if self.qr_reader_process and self.qr_reader_process.poll() is not None:
            self.root.after(0, self._qr_reader_stopped)
    
    def _qr_reader_stopped(self):
        """Called when QR Reader process stops"""
        returncode = self.qr_reader_process.poll() if self.qr_reader_process else None
        self.qr_reader_process = None
        self.qr_button.configure(text="QR Reader")
        self.status_label.configure(text=f"Status: QR Reader Exited (code: {returncode})")
        print(f"QR Reader process ended with code: {returncode}")
    
    def stop_qr_reader(self):
        """Stop the QR Reader process"""
        if self.qr_reader_process:
            print("Stopping QR Reader...")
            self.qr_reader_process.terminate()
            # Wait briefly for process to terminate
            try:
                self.qr_reader_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.qr_reader_process.kill()
            
            self.qr_reader_process = None
            self.qr_button.configure(text="QR Reader")
            self.status_label.configure(text="Status: QR Reader Stopped")
    
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
        
        # Stop other processes if they're running
        if self.qr_reader_process:
            self.stop_qr_reader()
            
        if self.model_ai_process:
            self.stop_model_ai()
            
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
        
        if self.qr_reader_process:
            self.stop_qr_reader()
            
        if self.model_ai_process:
            self.stop_model_ai()
            
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AIVisionGUI(root)
    root.mainloop()