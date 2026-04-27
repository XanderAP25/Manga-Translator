# main.py
import sys
import os
from src.core.chapter_manager import ChapterManager
from src.app import app
import ollama

def main(folder_path: str = None, progress_queue=None):
    # ----------------------------------------------------------------
    # Chapter mode (default): point at a folder of pages
    # ----------------------------------------------------------------
    if folder_path:
        chapter_dir = folder_path
    else:
        chapter_dir = os.path.join("data", "test_input", "Kisame_x_Rin")
    
    if not os.path.isdir(chapter_dir):
        print(f"Error: Could not find chapter folder '{chapter_dir}'")
        return

    # reference progressbar from app.py
    #prog_bar = app.progressbar

    manager = ChapterManager(chapter_dir, prog_bar=progress_queue)
    results = manager.run()

    # ----------------------------------------------------------------
    # Print a readable summary to the terminal
    # ----------------------------------------------------------------
    print("\n" + "=" * 50)
    print(f"  Chapter : {results['chapter']}")
    print(f"  Pages   : {results['total_pages']}")
    print(f"  Bubbles : {results['total_bubbles_translated']}")
    print(f"  Time    : {results['processing_time_seconds']}s")
    print("=" * 50)

    for page_name, bubbles in results["pages"].items():
        print(f"\n── {page_name} ({len(bubbles)} bubbles) ──")
        for bubble in bubbles:
            if "error" in bubble:
                print(f"  [ERROR] {bubble['error']}")
                continue
            print(f"  [{bubble['id']}] 🇯🇵 {bubble['raw']}")
            print(f"       🇺🇸 {bubble['translation']}")


if __name__ == "__main__":
    app.start_app()