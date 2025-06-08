#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import subprocess
import threading
import sys
import signal
import os
import io
import cv2
import numpy as np
from contextlib import redirect_stdout

# Replace tflite_runtime.interpreter with tensorflow
try:
    # First try to import from tflite_runtime
    import tflite_runtime.interpreter as tflite
    print("Using TFLite Runtime")
except ImportError:
    # If that fails, try to import from tensorflow
    try:
        import tensorflow as tf
        tflite = tf.lite.Interpreter
        print("Using TensorFlow Lite from full TensorFlow package")
    except ImportError:
        print("ERROR: Neither TensorFlow nor TFLite Runtime are installed")
        tflite = None

# Import functionality from the original program if needed
# from AIvisionProgram import run_camera

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
        self.model_path = None
        self.interpreter = None
        self.labels = []
        
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
        
        # Add model selection button
        self.model_button = ttk.Button(header_frame, text="Select Model",
                                     command=self.select_model, width=15)
        self.model_button.pack(side="right", padx=10)
        
        # Status indicator
        self.status_label = ttk.Label(main_frame, text="Status: Ready", 
                                    font=("Arial", 10))
        self.status_label.pack(anchor="w", padx=10, pady=5)
        
        # Model indicator
        self.model_label = ttk.Label(main_frame, text="Model: None selected", 
                                   font=("Arial", 10))
        self.model_label.pack(anchor="w", padx=10, pady=5)
        
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
    
    def select_model(self):
        """Open file dialog to select TensorFlow Lite model"""
        model_file = filedialog.askopenfilename(
            title="Select TensorFlow Lite Model",
            filetypes=[("TFLite files", "*.tflite"), ("All files", "*.*")]
        )
        
        if model_file:
            self.model_path = model_file
            model_name = os.path.basename(model_file)
            self.model_label.configure(text=f"Model: {model_name}")
            
            # Try to find a corresponding labels file
            labels_file = os.path.splitext(model_file)[0] + ".txt"
            if os.path.exists(labels_file):
                with open(labels_file, 'r') as f:
                    self.labels = [line.strip() for line in f.readlines()]
                print(f"Loaded {len(self.labels)} labels from {labels_file}")
            else:
                print("No labels file found. Using generic labels.")
                self.labels = [f"Class {i}" for i in range(10)]  # Generic labels
                
            # Load the TFLite model
            try:
                if tflite is None:
                    print("ERROR: TensorFlow Lite interpreter not available")
                    return
                    
                self.interpreter = tflite(model_path=self.model_path)
                self.interpreter.allocate_tensors()
                
                # Get input and output details
                input_details = self.interpreter.get_input_details()
                output_details = self.interpreter.get_output_details()
                
                print(f"Model loaded successfully.")
                print(f"Input shape: {input_details[0]['shape']}")
                print(f"Output shape: {output_details[0]['shape']}")
                
            except Exception as e:
                print(f"Error loading model: {e}")
                import traceback
                traceback.print_exc()
                self.interpreter = None
    
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
            
        if not self.model_path:
            print("Please select a TensorFlow Lite model first.")
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
        """Run the camera with TensorFlow Lite inference in a thread"""
        try:
            # Redirect stdout to capture output
            sys.stdout = self.stdout_redirect
            
            print("Starting AI camera with TensorFlow Lite model...")
            
            # Open camera using OpenCV
            cap = cv2.VideoCapture(0)  # 0 is usually the built-in camera
            
            if not cap.isOpened():
                print("Error: Could not open camera.")
                return
                
            # Get input details from the model
            input_details = self.interpreter.get_input_details()
            output_details = self.interpreter.get_output_details()
            
            height = input_details[0]['shape'][1]
            width = input_details[0]['shape'][2]
            
            floating_model = input_details[0]['dtype'] == np.float32
            
            print(f"Camera opened. Processing frames at {width}x{height}...")
            
            while self.camera_running:
                ret, frame = cap.read()
                
                if not ret:
                    print("Error: Could not read frame.")
                    break
                
                # Resize frame to expected dimensions
                resized_frame = cv2.resize(frame, (width, height))
                
                # Normalize pixel values if using a floating model
                input_data = np.expand_dims(resized_frame, axis=0)
                if floating_model:
                    input_data = (np.float32(input_data) - 127.5) / 127.5
                
                # Set input tensor
                self.interpreter.set_tensor(input_details[0]['index'], input_data)
                
                # Run inference
                self.interpreter.invoke()
                
                # Get output tensor
                output_data = self.interpreter.get_tensor(output_details[0]['index'])
                
                # Process results (this will vary based on model type)
                results = self._process_model_output(output_data, frame.shape[1], frame.shape[0])
                
                # Display the resulting frame with detections
                cv2.imshow('AI Vision Camera', frame)
                
                # Press 'q' to quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
            # Release resources
            cap.release()
            cv2.destroyAllWindows()
            
            # If we get here, process has ended
            self.root.after(0, self._camera_stopped)
            
        except Exception as e:
            print(f"Error running camera: {e}")
            import traceback
            traceback.print_exc()
            self.root.after(0, self._camera_stopped)
        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__
    
    def _process_model_output(self, output_data, img_width, img_height):
        """Process the output from the TensorFlow Lite model
        
        This is a placeholder implementation - modify based on your model type
        """
        # Detect model type based on output shape
        if len(output_data.shape) == 2:
            # Classification model
            return self._process_classification(output_data)
        elif len(output_data.shape) == 3 and output_data.shape[1] == 4:
            # Object detection model with bounding boxes
            return self._process_object_detection(output_data, img_width, img_height)
        else:
            print(f"Unknown model output shape: {output_data.shape}")
            return []
    
    def _process_classification(self, output_data):
        """Process classification model output"""
        # Get top prediction
        top_idx = np.argmax(output_data[0])
        top_score = output_data[0][top_idx]
        
        if top_idx < len(self.labels):
            label = self.labels[top_idx]
        else:
            label = f"Class {top_idx}"
            
        print(f"Detected: {label} (confidence: {top_score:.2f})")
        return [(label, top_score, None)]  # No bounding box for classification
    
    def _process_object_detection(self, output_data, img_width, img_height):
        """Process object detection model output"""
        results = []
        
        # This is a simplified implementation - adjust based on your model's output format
        # Typically: [batch, num_detections, 4] for boxes and [batch, num_detections] for scores
        for i in range(len(output_data[0])):
            score = float(output_data[0][i][4])
            
            # Skip low confidence detections
            if score < 0.5:
                continue
                
            # Get class index
            class_id = int(output_data[0][i][5])
            
            if class_id < len(self.labels):
                label = self.labels[class_id]
            else:
                label = f"Class {class_id}"
            
            # Get bounding box
            ymin = int(max(1, output_data[0][i][0] * img_height))
            xmin = int(max(1, output_data[0][i][1] * img_width))
            ymax = int(min(img_height, output_data[0][i][2] * img_height))
            xmax = int(min(img_width, output_data[0][i][3] * img_width))
            
            # Add detection to results
            results.append((label, score, (xmin, ymin, xmax, ymax)))
            print(f"Detected: {label} (confidence: {score:.2f})")
            
        return results
    
    def _camera_stopped(self):
        """Called when camera process stops"""
        self.camera_running = False
        self.start_button.configure(text="AI Vision")
        self.status_label.configure(text="Status: Ready")
        self.process = None
    
    def stop_camera(self):
        """Stop the camera process"""
        if self.camera_running:
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