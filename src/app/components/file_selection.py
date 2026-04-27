# src/components/file_selection.py
import customtkinter as ctk
from tkinter import filedialog

def select_folder():
    folder_path = filedialog.askdirectory(
        initialdir="/",
        title="Select a Folder"
    )
    print(f"Selected: {folder_path}")
    return folder_path
