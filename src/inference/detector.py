import numpy as np
from PIL import Image
from ultralytics import YOLO

class BubbleDetector:
    def __init__(self, model_path='./models/best.pt'):
        # Load once and keep in VRAM
        self.model = YOLO(model_path)

    def get_bubbles(self, img_path, conf=0.25):
        """
        Manually loads and normalizes the image to prevent 
        'Unable to infer channel dimension format' errors.
        """
        try:
            with Image.open(img_path) as img:
                # Force conversion to RGB to strip Alpha channels 
                # and normalize Grayscale/Indexed PNGs
                img_rgb = img.convert("RGB")
                img_array = np.array(img_rgb)
            
            # Passing the numpy array (H, W, 3) bypasses the path-based loader
            results = self.model.predict(
                source=img_array, 
                conf=conf, 
                device=0, 
                verbose=False
            )
            return results[0].boxes
        except Exception as e:
            print(f"Detector Error on {img_path}: {e}")
            return []