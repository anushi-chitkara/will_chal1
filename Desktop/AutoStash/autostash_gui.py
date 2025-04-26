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
        self.title("AutoStash – Smart GitHub Backups")
        self.geometry("600x650")
        self.resizable(False, False)

        # Managers
        self.config = ConfigManager()
        self.github = GitHubManager()
        self.backup = BackupManager()

        # Create ~/.autostash directory if it doesn't exist
        os.makedirs(os.path.expanduser("~/.autostash"), exist_ok=True)

        # GUI Elements
        self.create_widgets()
        self.load_saved_settings()
        
        # Check backup status when starting
        self.check_backup_status()

    def create_widgets(self):
        # Folders Frame
        self.folder_frame = ttk.LabelFrame(self, text="Folders to Back Up")
        self.folder_frame.pack(fill="x", padx=15, pady=10)

        self.folder_list = tk.Listbox(self.folder_frame, width=60, height=5, selectmode=tk.SINGLE)
        self.folder_list.pack(side="left", padx=10, pady=10)
        folder_btns = tk.Frame(self.folder_frame)
        folder_btns.pack(side="left", padx=5)
        ttk.Button(folder_btns, text="Add Folder", command=self.add_folder).pack(fill="x", pady=2)
        ttk.Button(folder_btns, text="Remove Selected", command=self.remove_folder).pack(fill="x", pady=2)

        # Separator
        ttk.Separator(self, orient='horizontal').pack(fill='x', padx=15, pady=10)

        # GitHub Frame
        self.repo_frame = ttk.LabelFrame(self, text="GitHub Repository")
        self.repo_frame.pack(fill="x", padx=15, pady=5)

        repo_inner = tk.Frame(self.repo_frame)
        repo_inner.pack(padx=10, pady=5, fill="x")
        ttk.Button(repo_inner, text="Connect GitHub", command=self.connect_github).pack(side="left")
        self.repo_combobox = ttk.Combobox(repo_inner, width=40, state="readonly")
        self.repo_combobox.pack(side="left", padx=10)
        self.github_status = tk.Label(self.repo_frame, text="Not connected", foreground="red")
        self.github_status.pack(anchor="w", padx=10)

        # Separator
        ttk.Separator(self, orient='horizontal').pack(fill='x', padx=15, pady=10)
        
        # Backup Options Frame
        self.options_frame = ttk.LabelFrame(self, text="Backup Options")
        self.options_frame.pack(fill="x", padx=15, pady=5)
        
        # System files backup option
        self.system_files_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.options_frame, text="Backup system files (/etc)", 
                        variable=self.system_files_var).pack(anchor="w", padx=10, pady=5)
        
        # Encryption option
        self.encrypt_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.options_frame, text="Encrypt backup with GPG", 
                        variable=self.encrypt_var).pack(anchor="w", padx=10, pady=5)
        
        # Separator
        ttk.Separator(self, orient='horizontal').pack(fill='x', padx=15, pady=10)

        # Schedule Frame
        self.schedule_frame = ttk.LabelFrame(self, text="Backup Schedule")
        self.schedule_frame.pack(fill="x", padx=15, pady=5)
        schedule_inner = tk.Frame(self.schedule_frame)
        schedule_inner.pack(padx=10, pady=5, fill="x")
        ttk.Label(schedule_inner, text="Frequency:").pack(side="left")
        self.schedule_combobox = ttk.Combobox(schedule_inner, values=["Daily", "Weekly"], width=15, state="readonly")
        self.schedule_combobox.current(0)
        self.schedule_combobox.pack(side="left", padx=10)
        ttk.Button(schedule_inner, text="Set Schedule", command=self.set_schedule).pack(side="left", padx=10)

        # Backup Status Frame
        self.status_frame = ttk.LabelFrame(self, text="Backup Status")
        self.status_frame.pack(fill="x", padx=15, pady=5)
        
        self.last_backup_label = ttk.Label(self.status_frame, text="No previous backups found")
        self.last_backup_label.pack(anchor="w", padx=10, pady=5)

        # Separator
        ttk.Separator(self, orient='horizontal').pack(fill='x', padx=15, pady=10)

        # Backup/Restore Frame
        action_frame = tk.Frame(self)
        action_frame.pack(pady=10)
        ttk.Button(action_frame, text="Run Backup Now", command=self.run_backup, width=18).pack(side="left", padx=10)
        ttk.Button(action_frame, text="Restore Latest Backup", command=self.restore_backup, width=20).pack(side="left", padx=10)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready.")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

    def check_backup_status(self):
        """Check last backup time and notify if overdue"""
        last_backup = self.backup.get_last_backup_time()
        
        if last_backup:
            try:
                backup_time = datetime.datetime.strptime(last_backup, "%Y-%m-%d %H:%M:%S")
                now = datetime.datetime.now()
                self.last_backup_label.config(text=f"Last backup: {backup_time.strftime('%Y-%m-%d %H:%M')}")
                
                # Check if backup is overdue (more than 24 hours)
                if (now - backup_time).total_seconds() > 24*60*60:
                    self.last_backup_label.config(foreground="red")
                    
                    # Send desktop notification
                    try:
                        days = (now - backup_time).days
                        subprocess.run([
                            "notify-send", 
                            "AutoStash Backup Overdue", 
                            f"Last backup was {days} days ago"
                        ])
                    except:
                        # If notify-send fails, just update the GUI
                        pass
                else:
                    self.last_backup_label.config(foreground="green")
            except Exception as e:
                self.last_backup_label.config(text=f"Error reading backup time: {str(e)}", foreground="red")
        else:
            self.last_backup_label.config(text="No previous backups found", foreground="orange")
        
        # Schedule this check to run again after 1 hour
        self.after(3600000, self.check_backup_status)

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder and folder not in self.folder_list.get(0, tk.END):
            self.folder_list.insert(tk.END, folder)
            self.config.save_folders(self.folder_list.get(0, tk.END))

    def remove_folder(self):
        sel = self.folder_list.curselection()
        if sel:
            self.folder_list.delete(sel)
            self.config.save_folders(self.folder_list.get(0, tk.END))

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
            self.github_status.config(text="Connected", foreground="green")
            self.status_var.set("GitHub connected. Select a repository.")
        except Exception as e:
            self.github_status.config(text="Failed to connect", foreground="red")
            self.status_var.set(f"GitHub error: {e}")

    def run_backup(self):
        folders = self.folder_list.get(0, tk.END)
        repo = self.repo_combobox.get()
        
        if not folders or not repo:
            messagebox.showerror("Missing Info", "Please select at least one folder and a GitHub repository.")
            return
            
        self.status_var.set("Running backup...")
        self.update_idletasks()
        
        try:
            # Get backup options
            backup_system = self.system_files_var.get()
            encrypt = self.encrypt_var.get()
            
            # Run backup with options
            self.backup.run(folders, repo, backup_system=backup_system, encrypt=encrypt)
            
            self.status_var.set("Backup completed successfully!")
            messagebox.showinfo("Backup", "Backup completed successfully!")
            
            # Update status display
            self.check_backup_status()
        except Exception as e:
            self.status_var.set(f"Backup failed: {e}")
            messagebox.showerror("Backup Failed", str(e))

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
            interval = "0 2 * * *"  # 2 AM every day
        elif freq == "Weekly":
            interval = "0 2 * * 0"  # 2 AM every Sunday
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

if __name__ == "__main__":
    app = AutoStashGUI()
    app.mainloop()

