# src/core/chapter_manager.py
import os
import json
import glob
import time
from src.core.processor import MangaProcessor
from src.utils.typesetter import MangaTypesetter

class ChapterManager:
    """
    Orchestrates processing of an entire chapter folder.
    Resume functionality has been removed; every run starts from page 1.
    """

    def __init__(self, chapter_dir: str, prog_bar=None):
        self.chapter_dir = chapter_dir
        self.prog_bar = prog_bar
        self.chapter_name = os.path.basename(chapter_dir.rstrip("/\\"))

        # Output to parent directory with "Translated " prefix
        parent_dir = os.path.dirname(chapter_dir)
        self.out_dir = os.path.join(parent_dir, "Translated " + self.chapter_name)
        os.makedirs(self.out_dir, exist_ok=True)

        self.results_path = os.path.join(self.out_dir, "results.json")

        # Discover pages once at init
        self.pages = self._discover_pages()

        print(f"[ChapterManager] Found {len(self.pages)} pages in '{self.chapter_name}'")

    def _discover_pages(self) -> list[str]:
        extensions = ("*.jpg", "*.jpeg", "*.png", "*.webp")
        found = []
        for ext in extensions:
            found.extend(glob.glob(os.path.join(self.chapter_dir, ext)))

        def page_sort_key(path):
            name = os.path.basename(path)
            digits = ""
            for ch in name:
                if ch.isdigit():
                    digits += ch
                elif digits:
                    break
            return int(digits) if digits else name

        return sorted(found, key=page_sort_key)

    def run(self) -> dict:
        """
        Process every page in the chapter.
        """
        print(f"\n[ChapterManager] Starting chapter: {self.chapter_name}")
        chapter_start = time.time()
        
        # Stores final data for all pages
        all_page_results = {}

        # Load models once for the whole chapter
        processor = MangaProcessor()

        for page_num, page_path in enumerate(self.pages, start=1):
            page_key = os.path.basename(page_path)

            print(f"  [{page_num:>3}/{len(self.pages)}] Processing {page_key} ...", end=" ", flush=True)
            page_start = time.time()
            if self.prog_bar:
                if page_num == len(self.pages):  # First page, initialize progress bar
                    current_val = 1
                else:
                    current_val = (page_num-1) / len(self.pages)
                self.prog_bar.put(current_val)  # Update progress bar based on page count
                
            try:
                page_results = processor.process_page(page_path)
                elapsed = time.time() - page_start
                print(f"{len(page_results)} bubbles — {elapsed:.1f}s")
            except Exception as e:
                print(f"ERROR: {e}")
                page_results = [{"error": str(e)}]

            all_page_results[page_key] = page_results

        # Assemble final output
        total_time = time.time() - chapter_start
        total_bubbles = sum(
            len([b for b in bubbles if "error" not in b])
            for bubbles in all_page_results.values()
        )

        chapter_output = {
            "chapter": self.chapter_name,
            "total_pages": len(self.pages),
            "total_bubbles_translated": total_bubbles,
            "processing_time_seconds": round(total_time, 2),
            "pages": all_page_results
        }

        with open(self.results_path, "w", encoding="utf-8") as f:
            json.dump(chapter_output, f, ensure_ascii=False, indent=2)

        # --- TYPESETTING PHASE ---
        print("\n[ChapterManager] Generating Typeset Images...")
        typesetter = MangaTypesetter()
        typeset_dir = os.path.join(self.out_dir, "typeset_pages")
        os.makedirs(typeset_dir, exist_ok=True)

        for page_path in self.pages:
            page_key = os.path.basename(page_path)
            if page_key in all_page_results:
                output_image_path = os.path.join(typeset_dir, page_key)
                typesetter.render_page(page_path, all_page_results[page_key], output_image_path)
                print(f"  Saved typeset: {page_key}")

        print(f"\n[ChapterManager] Done! {total_bubbles} bubbles across {len(self.pages)} pages.")
        return chapter_output