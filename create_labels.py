#!/usr/bin/env python3

"""
Script to create label files for common model types.
"""

import os
import argparse

# COCO dataset labels (common for object detection models)
COCO_LABELS = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 
    'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 
    'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 
    'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 
    'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 
    'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 
    'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 
    'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 
    'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 
    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 
    'toothbrush'
]

# ImageNet 1000 classes (common for classification models)
# This is a shortened version with just 20 classes for demonstration
IMAGENET_LABELS = [
    'tench', 'goldfish', 'great white shark', 'tiger shark', 'hammerhead shark',
    'electric ray', 'stingray', 'rooster', 'hen', 'ostrich', 'brambling',
    'goldfinch', 'house finch', 'junco', 'indigo bunting', 'American robin',
    'bulbul', 'jay', 'magpie', 'chickadee'
]

def create_label_file(model_path, label_type="coco"):
    """Create a label file for the given model"""
    base_path = os.path.splitext(model_path)[0]
    label_file = f"{base_path}.txt"
    
    if os.path.exists(label_file):
        print(f"Label file already exists: {label_file}")
        return
    
    if label_type.lower() == "coco":
        labels = COCO_LABELS
    elif label_type.lower() == "imagenet":
        labels = IMAGENET_LABELS
    else:
        print(f"Unknown label type: {label_type}")
        return
    
    with open(label_file, 'w') as f:
        for label in labels:
            f.write(f"{label}\n")
    
    print(f"Created label file: {label_file} with {len(labels)} labels")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create label files for TensorFlow Lite models")
    parser.add_argument("model_path", help="Path to the TensorFlow Lite model")
    parser.add_argument("--type", choices=["coco", "imagenet"], default="coco",
                        help="Type of labels to create (default: coco)")
    
    args = parser.parse_args()
    create_label_file(args.model_path, args.type)