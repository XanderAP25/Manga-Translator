# src/utils/typesetter.py
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont


class MangaTypesetter:
    """
    Erases original Japanese text and typesets English translations onto manga pages.

    Coordinate contract
    -------------------
    bbox values in results.json are always in ORIGINAL IMAGE pixel space.
    processor.py handles all scaling before storing them, so this class
    never needs to scale — it uses coordinates directly.
    """

    def __init__(self, font_path: str = "assets/fonts/manga_font.ttf"):
        self.font_path = font_path if os.path.exists(font_path) else None
        if not self.font_path:
            print(f"[Warning] Font not found at '{font_path}'. Using Pillow default.")

    # ------------------------------------------------------------------
    # Public: render one page
    # ------------------------------------------------------------------

    def render_page(self, img_path: str, page_data: list, output_path: str):
        """
        Open the source image (any format), erase each bubble's Japanese text,
        typeset the English translation, and save as PNG.

        Args:
            img_path:    Path to the original page image (jpg, png, webp, …).
            page_data:   List of bubble dicts from processor.py.
                         Each dict must have "bbox" and "translation".
            output_path: Where to save the finished image.
        """
        with Image.open(img_path) as img:
            # Normalise to RGB — handles grayscale, RGBA, palette-mode PNGs
            canvas = img.convert("RGB")

        draw = ImageDraw.Draw(canvas)

        for bubble in page_data:
            # Skip error entries
            if "error" in bubble or not bubble.get("translation"):
                continue

            x1, y1, x2, y2 = bubble["bbox"]

            # Clamp to canvas bounds (defensive — coords should already be valid)
            cw, ch = canvas.size
            x1 = max(0.0, min(x1, cw)) 
            y1 = max(0.0, min(y1, ch)) 
            x2 = max(0.0, min(x2, cw)) 
            y2 = max(0.0, min(y2, ch)) 

            if x2 <= x1 or y2 <= y1:
                continue  # degenerate box, skip

            # 1. White-out the original Japanese text (reduced by 5%)
            w = x2 - x1
            h = y2 - y1
            inset_x = 0.025 * w  # 2.5% on each side for 5% total reduction
            inset_y = 0.025 * h
            white_x1 = x1 + inset_x
            white_y1 = y1 + inset_y
            white_x2 = x2 - inset_x
            white_y2 = y2 - inset_y
            
            # Use rounded corners with radius based on 10% of the smaller dimension
            radius = min(white_x2 - white_x1, white_y2 - white_y1) * 0.1
            draw.rounded_rectangle([white_x1, white_y1, white_x2, white_y2], fill="white", radius=radius)

            # 2. Fit and draw the English translation
            self._draw_fitted_text(draw, white_x1, white_y1, white_x2, white_y2, bubble["translation"])

        # Always save as PDF to preserve quality regardless of source format
        out_pdf = self._ensure_pdf_ext(output_path)
        canvas.save(out_pdf, "PDF")
        return out_pdf

    # ------------------------------------------------------------------

    def _font(self, size: int) -> ImageFont.ImageFont:
        """Load the manga font at a given size, falling back to Pillow default."""
        if self.font_path:
            try:
                return ImageFont.truetype(self.font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    def _draw_fitted_text(
        self,
        draw: ImageDraw.ImageDraw,
        x1: float, y1: float, x2: float, y2: float,
        text: str,
    ):
        """
        Shrink font size until the wrapped text fits inside the bounding box,
        then centre it both horizontally and vertically.
        """
        box_w = x2 - x1
        box_h = y2 - y1
        PADDING = 4          # inner margin on each side
        inner_w = box_w - PADDING * 2
        inner_h = box_h - PADDING * 2

        if inner_w <= 0 or inner_h <= 0:
            return

        best_font   = None
        best_text   = text
        best_size   = 6

        # Try font sizes from large down to min, stop at first fit
        for size in range(40, 5, -2):
            font = self._font(size)

            # Estimate chars-per-line from the font's actual character width
            try:
                avg_char_w = font.getlength("A")
            except AttributeError:
                avg_char_w = size * 0.55

            chars_per_line = max(1, int(inner_w / avg_char_w))
            wrapped = textwrap.fill(text, width=chars_per_line)

            bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=2)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            if text_w <= inner_w and text_h <= inner_h:
                best_font = font
                best_text = wrapped
                best_size = size
                break

        # If nothing fit, use the smallest size with full wrapping anyway
        if best_font is None:
            best_font = self._font(6)
            try:
                avg_char_w = best_font.getlength("A")
            except AttributeError:
                avg_char_w = 6 * 0.55
            chars_per_line = max(1, int(inner_w / avg_char_w))
            best_text = textwrap.fill(text, width=chars_per_line)

        # Centre inside the box
        bbox = draw.multiline_textbbox((0, 0), best_text, font=best_font, spacing=2)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        text_x = x1 + PADDING + (inner_w - text_w) / 2
        text_y = y1 + PADDING + (inner_h - text_h) / 2

        draw.multiline_text(
            (text_x, text_y),
            best_text,
            font=best_font,
            fill="black",
            align="center",
            spacing=2,
        )

    @staticmethod
    def _ensure_pdf_ext(path: str) -> str:
        """Replace whatever extension is on the path with .pdf."""
        base, _ = os.path.splitext(path)
        return base + ".pdf"