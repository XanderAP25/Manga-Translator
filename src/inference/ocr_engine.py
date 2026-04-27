# src/inference/ocr_engine.py
from manga_ocr import MangaOcr

class OCREngine:
    """
    Wraps MangaOCR with both single-image and batch interfaces.
    """

    def __init__(self):
        # MangaOcr selects CUDA automatically if available
        self.mocr = MangaOcr()

    # ------------------------------------------------------------------
    # Single image (kept for backward compatibility with processor.py)
    # ------------------------------------------------------------------

    def extract_text(self, image_crop) -> str:
        """Extract text from a single PIL image crop."""
        return self.mocr(image_crop)

    # ------------------------------------------------------------------
    # Batch interface (used by the updated processor)
    # ------------------------------------------------------------------

    def extract_batch(self, image_crops: list) -> list[str]:
        """
        Extract text from a list of PIL image crops in a single GPU pass.

        Args:
            image_crops: List of PIL.Image objects (bubble crops from one page).

        Returns:
            List of strings in the same order as image_crops.
        """
        if not image_crops:
            return []

        # Single image — no batching overhead needed
        if len(image_crops) == 1:
            return [self.mocr(image_crops[0])]

        # --- True GPU batch via HuggingFace internals ---
        # mocr.processor  = the image feature extractor + tokenizer
        # mocr.model      = the VisionEncoderDecoder sitting on CUDA

        # Step 1: Detect the correct attribute for image processing
        # Some versions use .processor, some use .feature_extractor
        proc = getattr(self.mocr, 'processor', None) or getattr(self.mocr, 'feature_extractor', None)
        
        if proc is None:
            raise AttributeError("MangaOcr object has no recognizable 'processor' or 'feature_extractor'")

        # Step 2: Convert all PIL crops into a single stacked pixel tensor
        inputs = proc(images=image_crops, return_tensors="pt")
        pixel_values = inputs.pixel_values.to(self.mocr.model.device)

        # Step 3: One forward pass — all crops processed in parallel on GPU
        generated_ids = self.mocr.model.generate(pixel_values)

        # Step 4: Decode output tokens back to strings
        texts = self.mocr.tokenizer.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )

        return texts