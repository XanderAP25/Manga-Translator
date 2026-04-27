# src/app/app.py
import sys
import os
import customtkinter
from .components.file_selection import select_folder
from main import main
import threading
import queue
from fractions import Fraction

def start_app():
    def folder_button_callback():
        
        folder_path = select_folder()
        if folder_path:
            chosen_folder_textbox.configure(state="normal")  # Make it editable to update text
            chosen_folder_textbox.delete("0.0", customtkinter.END)  # Clear existing text
            chosen_folder_textbox.insert("0.0", folder_path)  # Insert new path
            chosen_folder_textbox.configure(state="disabled")  # Make it read-only again

    def run_program_callback():
        folder = chosen_folder_textbox.get("0.0", customtkinter.END).strip()
        if not folder or "No folder selected" in folder:
            return
        
        progressbar.place(relx=0.5, rely=0.95, anchor=customtkinter.CENTER)
        progressbar.set(0)

        progress_labal.place(relx=0.5, rely=0.98, anchor=customtkinter.CENTER)
        progress_labal.configure(text="Processing...")

        progress_queue = queue.Queue()

        def check_progress():
            try:
                while True:
                    value = progress_queue.get_nowait()
                    progressbar.set(value)
                    if value >= 1.0:
                        progress_labal.configure(text="Complete!")
                    else:
                        progress_labal.configure(text=f"{value*100:.2f}% Complete")
                    
            except queue.Empty:
                pass
            app.after(100, check_progress)  # Check every 100ms

        check_progress()  # Start checking progress

        run_button.configure(state="disabled")

        def thread_target():
            main(folder, progress_queue)
            app.after(0, lambda: run_button.configure(state="normal", text="Run Program"))
            app.after(0, lambda: progressbar.set(1.0))  # Set to 100% when done
            app.after
        
        threading.Thread(target=thread_target, daemon=True).start()

    app = customtkinter.CTk()
    app.title("Manga Translator")
    app.geometry("640x480")

    welcome_banner_label = customtkinter.CTkLabel(app, text="Manga Translator", font=customtkinter.CTkFont(size=40, weight="bold"))
    description_label = customtkinter.CTkLabel(app, text="Translate Japanese manga to English", font=customtkinter.CTkFont(size=16))
    chosen_folder_textbox = customtkinter.CTkTextbox(app, width=400, height=30)

    chosen_folder_textbox.insert("0.0", "No folder selected yet...")
    chosen_folder_textbox.configure(state="disabled")  # Make it read-only

    run_button = customtkinter.CTkButton(app, text="Run Program", command=run_program_callback,
                                         fg_color="#9B1414", hover_color="#45A049")

    folder_button = customtkinter.CTkButton(app, text="Select Folder of Manga Panels", command=folder_button_callback,
                                            fg_color="#1F2797", hover_color="#7A9BD8")

    folder_button.place(relx=0.335, rely=0.9, anchor=customtkinter.CENTER)
    run_button.place(relx=0.7, rely=0.9, anchor=customtkinter.CENTER)
    chosen_folder_textbox.place(relx=0.5, rely=0.83, anchor=customtkinter.CENTER)

    welcome_banner_label.pack(pady=5)
    description_label.pack(pady=1)

    guidelines_label = customtkinter.CTkLabel(app, text="How to Use:\n1. Select a folder containing manga page images.\n" \
    "2. Click 'Run Program' to start the translation process.\n3. Wait for the progress bar to complete." \
    "\n4. View the translated results in the output folder.", font=customtkinter.CTkFont(size=20), justify="left")
    guidelines_label.pack(pady=10)

    guidelines_label.place(relx=0.5, rely=0.35, anchor=customtkinter.CENTER)
    
    progress_labal = customtkinter.CTkLabel(app, text="of", font=customtkinter.CTkFont(size=14))

    output_info_label = customtkinter.CTkLabel(app, text="Translated pages will be saved in the same parent folder with 'Translated ' prefix.", font=customtkinter.CTkFont(size=12), justify="center")
    output_info_label.place(relx=0.5, rely=0.77, anchor=customtkinter.CENTER)

    progressbar = customtkinter.CTkProgressBar(app, width=400, height=15)
    progressbar.set(0)  # Start at 0%

    app.mainloop()