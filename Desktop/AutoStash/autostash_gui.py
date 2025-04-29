import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import keyring
import datetime
import os
import subprocess

from github_integration import GitHubManager
from backup_logic import BackupManager
from config_manager import ConfigManager
import scheduler

class AutoStashGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Autostash - A Linux Admin Smart Backup System")
        self.geometry("800x1000")
        self.minsize(800, 1000)
        self.configure(bg="#f7f7f7")
        self.option_add("*Font", "Arial 11")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabelframe", background="#f7f7f7", borderwidth=0)
        style.configure("TLabelframe.Label", font=("Arial", 12, "bold"), background="#f7f7f7")
        style.configure("TLabel", background="#f7f7f7")
        style.configure("TButton", font=("Arial", 10, "bold"), padding=6)
        style.configure("TCheckbutton", background="#f7f7f7", font=("Arial", 10))
        style.configure("TCombobox", fieldbackground="#fff", background="#fff")
        style.configure("TProgressbar", thickness=18, troughcolor="#e0e0e0", background="#3498db", bordercolor="#bdc3c7", lightcolor="#5dade2", darkcolor="#2980b9")

        self.config = ConfigManager()
        self.github = GitHubManager()
        self.backup = BackupManager()

        os.makedirs(os.path.expanduser("~/.autostash"), exist_ok=True)
        self.create_widgets()
        self.load_saved_settings()
        self.load_backup_timeline()
        self.check_backup_status()

    def create_widgets(self):
        title_label = tk.Label(self, text="Autostash", font=("Arial", 22, "bold"), bg="#f7f7f7", fg="#2d3436")
        title_label.pack(pady=(18, 10))

        # Folders Frame
        self.folder_frame = ttk.LabelFrame(self, text="Folders to Back Up")
        self.folder_frame.pack(fill="x", padx=18, pady=10, ipady=8)
        folder_inner = tk.Frame(self.folder_frame, bg="#f7f7f7")
        folder_inner.pack(fill="x", padx=10, pady=5)
        self.folder_entry = tk.Entry(folder_inner, width=55, font=("Arial", 11))
        self.folder_entry.pack(side="left", padx=(0, 8), pady=5)
        ttk.Button(folder_inner, text="Add Folder", command=self.add_folder).pack(side="left", padx=(0, 8))
        tk.Button(folder_inner, text="Remove", command=self.remove_folder, bg="#e74c3c", fg="white", 
                 font=("Arial", 10, "bold"), width=8, relief="flat").pack(side="left")
        self.folder_list = tk.Listbox(self.folder_frame, width=95, height=2, font=("Arial", 10))
        self.folder_list.pack(fill="x", padx=10, pady=(8, 2))

        # GitHub Frame
        self.repo_frame = ttk.LabelFrame(self, text="GitHub Repository")
        self.repo_frame.pack(fill="x", padx=18, pady=10, ipady=8)
        repo_inner = tk.Frame(self.repo_frame, bg="#f7f7f7")
        repo_inner.pack(fill="x", padx=10, pady=5)
        self.repo_combobox = ttk.Combobox(repo_inner, width=38, state="readonly")
        self.repo_combobox.pack(side="left", padx=(0, 8), pady=5)
        ttk.Button(repo_inner, text="Connect GitHub", command=self.connect_github).pack(side="left")
        self.github_status = tk.Label(self.repo_frame, text="Not connected", fg="#c0392b", 
                                     bg="#f7f7f7", font=("Arial", 10, "bold"))
        self.github_status.pack(anchor="w", padx=10, pady=(2, 0))

        # Backup Options Frame
        self.options_frame = ttk.LabelFrame(self, text="Backup Options")
        self.options_frame.pack(fill="x", padx=18, pady=10, ipady=8)
        self.system_files_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.options_frame, text="Backup system files (/etc)", 
                      variable=self.system_files_var, bg="#f7f7f7", font=("Arial", 10)).pack(anchor="w", padx=10, pady=3)

        # Progress Frame
        self.progress_frame = ttk.LabelFrame(self, text="Backup Progress")
        self.progress_frame.pack(fill="x", padx=18, pady=10, ipady=8)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, 
                                           maximum=100, style="TProgressbar")
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_text = tk.Label(self.progress_frame, text="", bg="#f7f7f7", fg="#2d3436",
                                     font=("Arial", 9))
        self.progress_text.pack()

        # Enhanced Backup Timeline Frame with Scrollbar
        self.timeline_frame = ttk.LabelFrame(self, text="Backup History")
        self.timeline_frame.pack(fill="both", expand=True, padx=18, pady=10, ipady=8)
        
        # Container frame for listbox and scrollbar
        timeline_container = tk.Frame(self.timeline_frame, bg="#f7f7f7")
        timeline_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Scrollbar
        self.timeline_scroll = ttk.Scrollbar(timeline_container)
        self.timeline_scroll.pack(side="right", fill="y")

        # Listbox with scrollbar
        self.timeline_list = tk.Listbox(
            timeline_container, 
            yscrollcommand=self.timeline_scroll.set,
            width=110, 
            height=5,
            font=("Monospace", 9),
            bg="#ffffff",
            selectbackground="#e0f3ff",
            relief="flat"
        )
        self.timeline_list.pack(side="left", fill="both", expand=True)
        self.timeline_scroll.config(command=self.timeline_list.yview)

        # Heading for Backup History
        self.heading_label = tk.Label(self.timeline_frame, text="Latest Backup Entries", font=("Arial", 14, "bold"), bg="#f7f7f7")
        self.heading_label.pack(pady=(5, 0))

        # Date and Time Label
        self.date_time_label = tk.Label(self.timeline_frame, text="Date and Time", font=("Arial", 12, "italic"), bg="#f7f7f7")
        self.date_time_label.pack(pady=(5, 0))

        # Action Buttons
        action_frame = tk.Frame(self, bg="#f7f7f7")
        action_frame.pack(pady=18)
        run_btn = tk.Button(action_frame, text="Run Backup", bg="#27ae60", fg="white", 
                          font=("Arial", 12, "bold"), width=18, relief="flat", command=self.run_backup)
        run_btn.pack(side="left", padx=22)
        restore_btn = tk.Button(action_frame, text="Restore Backup", bg="#2980b9", fg="white", 
                              font=("Arial", 12, "bold"), width=18, relief="flat", command=self.restore_backup)
        restore_btn.pack(side="left", padx=22)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready.")
        self.status_bar = tk.Label(self, textvariable=self.status_var, bg="#dfe6e9", 
                                 fg="#636e72", anchor="w", font=("Arial", 10))
        self.status_bar.pack(side="bottom", fill="x")

    def load_backup_timeline(self):
        self.timeline_list.delete(0, tk.END)
        history_path = os.path.expanduser("~/.autostash/backup_history")
        if os.path.exists(history_path):
            with open(history_path, "r") as f:
                lines = f.readlines()
                # Reverse the order of entries
                for line in reversed(lines):
                    self.timeline_list.insert(tk.END, line.strip())

    # Remaining methods remain unchanged...

if __name__ == "__main__":
    app = AutoStashGUI()
    app.mainloop()

