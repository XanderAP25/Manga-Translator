# src/core/processor.py
import asyncio
from PIL import Image
from src.inference.detector import BubbleDetector
from src.inference.ocr_engine import OCREngine
from src.inference.translator import NuanceTranslator


class MangaProcessor:
    """
    Processes a single manga page through the full MTL pipeline.

    Pipeline per page:
        detect bubbles → crop all → batch OCR → async translate all → return
    """

    def __init__(self):
        self.detector   = BubbleDetector()
        self.ocr        = OCREngine()
        self.translator = NuanceTranslator()

    def process_page(self, img_path: str) -> list[dict]:
        """
        Public entry point. Synchronous wrapper around the async pipeline
        so ChapterManager and main.py don't need to know about asyncio.
        """
        return asyncio.run(self._process_page_async(img_path))

    async def _process_page_async(self, img_path: str) -> list[dict]:
        # Step 0: Open and normalize image
        with Image.open(img_path) as img:
            img = img.convert("RGB")
            orig_w, orig_h = img.size

        # Step 1: Detect.
        boxes = self.detector.get_bubbles(img_path)
        if not boxes: 
            return []

        # Step 2: Scaling Factor
        # Ensure this matches the imgsz your YOLO model was trained on (usually 640)
        detector_dim = 640
        scale_x = orig_w / detector_dim
        scale_y = orig_h / detector_dim

        # SORTING: Group by Y (rows) and then Right-to-Left (X)
        sorted_indices = sorted(range(len(boxes)), 
                            key=lambda i: (round(boxes[i].xyxy[0][1].item() / 50), 
                                           -boxes[i].xyxy[0][0].item()))
        
        crops = []
        coords_list = []
        for i in sorted_indices:
            raw_coords = boxes[i].xyxy[0].tolist()
            
            # Extract and Scale
            x1_raw, y1_raw, x2_raw, y2_raw = raw_coords
            
            # MAGNITUDE CHECK: Prevents the "6000px" explosion
            # If the raw value is already larger than the detector_dim, 
            # the model likely returned absolute pixels already.
            if any(c > detector_dim for c in raw_coords):
                # Use as-is, just normalize the order
                left = min(raw_coords[0], raw_coords[2])
                top = min(raw_coords[1], raw_coords[3])
                right = max(raw_coords[0], raw_coords[2])
                bottom = max(raw_coords[1], raw_coords[3])
            else:
                # Standardize order then apply scaling ratio
                left = min(raw_coords[0], raw_coords[2]) * scale_x
                top = min(raw_coords[1], raw_coords[3]) * scale_y
                right = max(raw_coords[0], raw_coords[2]) * scale_x
                bottom = max(raw_coords[1], raw_coords[3]) * scale_y

            # Apply padding and clamp to image boundaries
            pad = 5
            crop_left = max(0, left - pad)
            crop_top = max(0, top - pad)
            crop_right = min(orig_w, right + pad)
            crop_bottom = min(orig_h, bottom + pad)

            # Safety check: If the box is still invalid (zero width/height), skip it
            if crop_right <= crop_left or crop_bottom <= crop_top:
                continue
            
            crops.append(img.crop((crop_left, crop_top, crop_right, crop_bottom)))
            coords_list.append([left, top, right, bottom])

        # Step 3: Batch OCR
        if not crops: return []
        raw_texts = self.ocr.extract_batch(crops)

        # Step 4: Concurrent Translation
        translation_tasks = [self.translator.translate_async(text) for text in raw_texts]
        translations = await asyncio.gather(*translation_tasks, return_exceptions=True)

        # Step 5: Assemble
        page_data = []
        for i, (coords, raw_text, trans_result) in enumerate(zip(coords_list, raw_texts, translations)):
            if isinstance(trans_result, Exception):
                trans_data = {"translation": "[Error]"}
            else:
                trans_data = trans_result

            page_data.append({
                "id":          i,
                "bbox":        coords,
                "raw":         raw_text,
                "translation": trans_data.get("translation", ""),
            })

        return page_data