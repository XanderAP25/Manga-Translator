# Manga Translator

Manga Translator is a desktop application that automates the translation of Japanese manga pages into English. It leverages state-of-the-art OCR, object detection, and large language models to detect speech bubbles, extract Japanese text, translate it, and typeset the English translation back onto the manga pages.

## Features

- **Automatic Bubble Detection:** Uses a YOLO-based model to detect speech bubbles in manga images.
- **High-Accuracy OCR:** Extracts Japanese text from detected bubbles using MangaOCR (GPU-accelerated).
- **AI-Powered Translation:** Translates Japanese text to English using a local Ollama LLM (default: translategemma:12b), with special handling for manga dialogue and proper nouns.
- **Typesetting:** Erases original Japanese text and overlays the English translation, preserving the manga's visual style.
- **Batch Processing:** Processes entire folders (chapters) of manga pages at once.
- **User-Friendly GUI:** Simple interface for selecting folders and running the translation pipeline.

## How It Works

1. **Select a Folder:** Choose a folder containing manga page images (JPG, PNG, WEBP).
2. **Run Program:** The app detects bubbles, extracts and translates text, and typesets the results.
3. **Output:** Translated pages are saved as PDFs in a new folder prefixed with `Translated ` in the same parent directory. A `results.json` file with all translations is also generated.

## Installation

1. **Clone the repository:**
	```sh
	git clone <repo-url>
	cd Manga-Translator
	```
2. **Install dependencies:**
	```sh
	pip install -r requirements.txt
	```
3. **Download YOLO Model:**
	Place your trained YOLO model (e.g., `best.pt`) in the `models/` directory.
4. **Ollama Model:**
	Ensure you have [Ollama](https://ollama.com/) installed and running locally. The app will automatically pull the required model (`translategemma:12b`) if not present. It is recommended to have at least 16 gb of VRAM available for this model.
5. **Fonts:**
	Place a suitable manga-style TTF font in `assets/fonts/manga_font.ttf` (optional, falls back to default if missing).

## Usage

1. **Start the Application:**
	```sh
	python main.py
	```
2. **Select the folder** containing manga images when prompted.
3. **Click 'Run Program'** to begin translation.
4. **Wait for completion.** Progress is shown in the GUI.
5. **Find results** in the new `Translated <chapter>` folder alongside your original images.

## Project Structure

- `main.py` — Entry point for the GUI application
- `src/app/app.py` — Main application logic and GUI
- `src/core/` — Core processing pipeline (chapter manager, processor)
- `src/inference/` — Bubble detection, OCR, and translation modules
- `src/utils/typesetter.py` — Typesetting logic for overlaying translations
- `models/` — Place YOLO model weights here (e.g., `best.pt`)
- `data/` — (Optional) For storing input/output data
- `assets/fonts/` — Custom manga font (optional)

## Requirements

- Python 3.8+
- [MangaOCR](https://github.com/kha-white/manga-ocr)
- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics)
- [Ollama](https://ollama.com/) (for LLM translation)
- [Pillow](https://python-pillow.org/)
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) (for GUI)

Install all Python dependencies with `pip install -r requirements.txt`.

## Notes

- The translation model runs locally via Ollama; no API keys or internet connection required after setup.
- For best results, use high-quality manga scans and a well-trained YOLO model for bubble detection.
- The application is designed for Japanese-to-English translation but can be adapted for other languages with minor changes.

## License

This project is for educational and personal use. Please respect the copyright of original manga creators.
