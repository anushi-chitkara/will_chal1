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
        tk.Button(folder_inner, text="Remove", command=self.remove_folder, bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), width=8, relief="flat").pack(side="left")
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

        self.github_status = tk.Label(self.repo_frame, text="Not connected", fg="#c0392b", bg="#f7f7f7", font=("Arial", 10, "bold"))
        self.github_status.pack(anchor="w", padx=10, pady=(2, 0))

        # Backup Options Frame
        self.options_frame = ttk.LabelFrame(self, text="Backup Options")
        self.options_frame.pack(fill="x", padx=18, pady=10, ipady=8)
        self.system_files_var = tk.BooleanVar(value=False)
        self.encrypt_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.options_frame, text="Backup system files (/etc)", variable=self.system_files_var, bg="#f7f7f7", font=("Arial", 10)).pack(anchor="w", padx=10, pady=3)
        tk.Checkbutton(self.options_frame, text="Encrypt backup with GPG", variable=self.encrypt_var, bg="#f7f7f7", font=("Arial", 10)).pack(anchor="w", padx=10, pady=3)

        # Schedule Frame
        self.schedule_frame = ttk.LabelFrame(self, text="Backup Schedule")
        self.schedule_frame.pack(fill="x", padx=18, pady=10, ipady=8)
        schedule_inner = tk.Frame(self.schedule_frame, bg="#f7f7f7")
        schedule_inner.pack(fill="x", padx=10, pady=5)
        tk.Label(schedule_inner, text="Frequency:", bg="#f7f7f7", font=("Arial", 10)).pack(side="left")
        self.schedule_combobox = ttk.Combobox(schedule_inner, values=["Daily", "Weekly"], width=14, state="readonly")
        self.schedule_combobox.current(0)
        self.schedule_combobox.pack(side="left", padx=(8, 8))
        ttk.Button(schedule_inner, text="Set Schedule", command=self.set_schedule).pack(side="left")

        # Backup Status Frame
        self.status_frame = ttk.LabelFrame(self, text="Backup Status")
        self.status_frame.pack(fill="x", padx=18, pady=10, ipady=8)
        self.last_backup_label = tk.Label(self.status_frame, text="No previous backups found", fg="#c0392b", bg="#f7f7f7", font=("Arial", 10, "bold"))
        self.last_backup_label.pack(anchor="w", padx=10, pady=5)

        # Progress Bar Frame
        self.progress_frame = ttk.LabelFrame(self, text="Backup Progress")
        self.progress_frame.pack(fill="x", padx=18, pady=10, ipady=8)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100, style="TProgressbar")
        self.progress_bar.pack(fill="x", padx=10, pady=10)

        # Backup Timeline Frame WITH SCROLLBAR, LATEST ENTRIES ON TOP
        self.timeline_frame = ttk.LabelFrame(self, text="Backup Timeline")
        self.timeline_frame.pack(fill="x", padx=18, pady=10, ipady=8)
        timeline_inner = tk.Frame(self.timeline_frame, bg="#f7f7f7")
        timeline_inner.pack(fill="x", padx=0, pady=0)
        self.timeline_scrollbar = tk.Scrollbar(timeline_inner, orient="vertical")
        self.timeline_list = tk.Listbox(timeline_inner, width=110, height=5, font=("Arial", 10), yscrollcommand=self.timeline_scrollbar.set)
        self.timeline_scrollbar.config(command=self.timeline_list.yview)
        self.timeline_list.pack(side="left", fill="both", expand=True, padx=(10,0), pady=5)
        self.timeline_scrollbar.pack(side="left", fill="y", pady=5)

        # Action Buttons (Modern style)
        action_frame = tk.Frame(self, bg="#f7f7f7")
        action_frame.pack(pady=18)
        run_btn = tk.Button(action_frame, text="Run Backup", bg="#27ae60", fg="white", font=("Arial", 12, "bold"), width=18, relief="flat", command=self.run_backup, activebackground="#219150")
        run_btn.pack(side="left", padx=22)
        restore_btn = tk.Button(action_frame, text="Restore Backup", bg="#2980b9", fg="white", font=("Arial", 12, "bold"), width=18, relief="flat", command=self.restore_backup, activebackground="#2471a3")
        restore_btn.pack(side="left", padx=22)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready.")
        self.status_bar = tk.Label(self, textvariable=self.status_var, bg="#dfe6e9", fg="#636e72", anchor="w", font=("Arial", 10))
        self.status_bar.pack(side="bottom", fill="x")

    def check_backup_status(self):
        last_backup = self.backup.get_last_backup_time()
        if last_backup:
            try:
                backup_time = datetime.datetime.strptime(last_backup, "%Y-%m-%d %H:%M:%S")
                now = datetime.datetime.now()
                self.last_backup_label.config(text=f"Last backup: {backup_time.strftime('%Y-%m-%d %H:%M')}", fg="#c0392b")
                if (now - backup_time).total_seconds() > 24 * 60 * 60:
                    self.last_backup_label.config(fg="#c0392b")
                    try:
                        days = (now - backup_time).days
                        subprocess.run([
                            "notify-send", 
                            "AutoStash Backup Overdue", 
                            f"Last backup was {days} days ago"
                        ])
                    except:
                        pass
                else:
                    self.last_backup_label.config(fg="#27ae60")
            except Exception as e:
                self.last_backup_label.config(text=f"Error reading backup time: {str(e)}", fg="#c0392b")
        else:
            self.last_backup_label.config(text="No previous backups found", fg="#c0392b")
        self.after(3600000, self.check_backup_status)

    def load_backup_timeline(self):
        self.timeline_list.delete(0, tk.END)
        history_path = os.path.expanduser("~/.autostash/backup_history")
        if os.path.exists(history_path):
            with open(history_path, "r") as f:
                lines = [line.strip() for line in f if line.strip()]
            # Show latest entries at the top
            for line in reversed(lines):
                self.timeline_list.insert(tk.END, line)

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder and folder not in self.folder_list.get(0, tk.END):
            self.folder_list.insert(tk.END, folder)
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self.config.save_folders(self.folder_list.get(0, tk.END))

    def remove_folder(self):
        sel = self.folder_list.curselection()
        if sel:
            self.folder_list.delete(sel)
            self.config.save_folders(self.folder_list.get(0, tk.END))
            self.folder_entry.delete(0, tk.END)

    def connect_github(self):
        token = keyring.get_password("autostash", "github_token")
        if not token:
            from tkinter.simpledialog import askstring
            token = askstring("GitHub Token", "Enter your GitHub Personal Access Token:", show='*')
            if not token:
                self.status_var.set("GitHub connection cancelled.")
                return
            keyring.set_password("autostash", "github_token", token)
        try:
            self.github.authenticate(token)
            repos = self.github.get_repos()
            self.repo_combobox['values'] = repos
            if repos:
                self.repo_combobox.current(0)
            self.github_status.config(text="Connected", fg="#27ae60")
            self.status_var.set("GitHub connected. Select a repository.")
        except Exception as e:
            self.github_status.config(text="Failed to connect", fg="#c0392b")
            self.status_var.set(f"GitHub error: {e}")

    def run_backup(self):
        folders = self.folder_list.get(0, tk.END)
        repo = self.repo_combobox.get()
        if not folders or not repo:
            messagebox.showerror("Missing Info", "Please select at least one folder and a GitHub repository.")
            return
        self.status_var.set("Running backup...")
        self.update_idletasks()
        self.progress_var.set(0)
        self.progress_bar.update()

        def progress_callback(percent, *args):  # <-- FIXED: accepts extra args
            self.progress_var.set(percent)
            self.progress_bar.update()

        try:
            backup_system = self.system_files_var.get()
            # encrypt = self.encrypt_var.get()  # encryption not used
            self.backup.run(
                folders, repo,
                backup_system=backup_system,
                # encrypt=encrypt,  # encryption not used
                progress_callback=progress_callback
            )
            self.status_var.set("Backup completed successfully!")
            messagebox.showinfo("Backup", "Backup completed successfully!")
            self.check_backup_status()
            self.progress_var.set(100)
            self.load_backup_timeline()
        except Exception as e:
            self.status_var.set(f"Backup failed: {e}")
            messagebox.showerror("Backup Failed", str(e))
            self.progress_var.set(0)

    def restore_backup(self):
        repo = self.repo_combobox.get()
        if not repo:
            messagebox.showerror("Missing Repo", "Please select a GitHub repository first.")
            return
        self.status_var.set("Restoring backup...")
        self.update_idletasks()
        try:
            restore_path = self.backup.restore(repo)
            self.status_var.set("Restore completed successfully!")
            messagebox.showinfo("Restore", f"Restore completed successfully to {restore_path}!")
        except Exception as e:
            self.status_var.set(f"Restore failed: {e}")
            messagebox.showerror("Restore Failed", str(e))

    def set_schedule(self):
        freq = self.schedule_combobox.get()
        if freq == "Daily":
            interval = "0 2 * * *"
        elif freq == "Weekly":
            interval = "0 2 * * 0"
        else:
            interval = "0 2 * * *"
        try:
            scheduler.setup_schedule(interval, os.path.abspath(__file__))
            self.status_var.set(f"Scheduled backups: {freq.lower()}.")
            messagebox.showinfo("Schedule", f"Backups scheduled: {freq}.")
        except Exception as e:
            self.status_var.set(f"Schedule failed: {e}")
            messagebox.showerror("Schedule Failed", str(e))

    def load_saved_settings(self):
        folders = self.config.get_folders()
        for folder in folders:
            self.folder_list.insert(tk.END, folder)
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)

if __name__ == "__main__":
    app = AutoStashGUI()
    app.mainloop()

