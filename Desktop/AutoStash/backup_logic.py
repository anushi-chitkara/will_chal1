import os
import shutil
import requests
import hashlib
import logging
import datetime
import subprocess
from git import Repo, GitCommandError
from github import GithubException

class BackupManager:
    def __init__(self):
        self.repo_path = os.path.expanduser("~/.autostash_repo")
        self.repo = None
        self.log_path = "/var/log/autostash"
        self._setup_logging()

    def _setup_logging(self):
        try:
            if not os.path.exists(self.log_path):
                try:
                    os.makedirs(self.log_path, exist_ok=True)
                except PermissionError:
                    subprocess.run(["sudo", "mkdir", "-p", self.log_path])
                    subprocess.run(["sudo", "chown", f"{os.getenv('USER')}:", self.log_path])
            self.logger = logging.getLogger('autostash')
            self.logger.setLevel(logging.INFO)
            handler = logging.FileHandler(os.path.join(self.log_path, "backup.log"))
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        except Exception as e:
            os.makedirs(os.path.expanduser("~/.autostash/logs"), exist_ok=True)
            self.logger = logging.getLogger('autostash')
            self.logger.setLevel(logging.INFO)
            handler = logging.FileHandler(os.path.expanduser("~/.autostash/logs/backup.log"))
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            print(f"Using fallback log location due to: {str(e)}")

    def run(self, folders, repo_name, backup_system=False, progress_callback=None):
        try:
            self.logger.info(f"Starting backup to {repo_name}")
            steps = len(folders)
            if backup_system:
                steps += 1
            completed = 0

            if not self._repo_exists(repo_name):
                self.logger.error(f"Repository {repo_name} doesn't exist or no access")
                raise Exception(f"Repository {repo_name} doesn't exist or you don't have access")

            self._prepare_repo(repo_name)

            for folder in folders:
                self.logger.info(f"Backing up: {folder}")
                self._sync_folder(folder)
                completed += 1
                if progress_callback:
                    progress_callback(completed / steps * 100)

            if backup_system:
                self.logger.info("Backing up system files")
                self._backup_system_files()
                completed += 1
                if progress_callback:
                    progress_callback(completed / steps * 100)

            self._git_commit_push()
            self._record_backup_time()
            self.logger.info("Backup completed successfully")
            self._append_backup_history()

        except Exception as e:
            self.logger.error(f"Backup failed: {str(e)}")
            raise Exception(f"Backup failed: {str(e)}")

    def _record_backup_time(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(os.path.expanduser("~/.autostash/last_backup"), "w") as f:
            f.write(timestamp)

    def _append_backup_history(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(os.path.expanduser("~/.autostash/backup_history"), "a") as f:
            f.write(timestamp + "\n")

    def _backup_system_files(self):
        system_backup_path = os.path.join(self.repo_path, "system_config")
        os.makedirs(system_backup_path, exist_ok=True)
        critical_files = [
            "/etc/fstab",
            "/etc/hosts",
            "/etc/passwd"
        ]
        for file_path in critical_files:
            if os.path.exists(file_path):
                try:
                    dest_dir = os.path.join(system_backup_path, os.path.dirname(file_path)[1:])
                    os.makedirs(dest_dir, exist_ok=True)
                    shutil.copy2(file_path, os.path.join(dest_dir, os.path.basename(file_path)))
                    self.logger.info(f"Backed up: {file_path}")
                except PermissionError:
                    self.logger.warning(f"Permission denied for: {file_path}")
                except Exception as e:
                    self.logger.error(f"Failed to backup {file_path}: {str(e)}")

    def _repo_exists(self, repo_name):
        url = f"https://github.com/{repo_name}"
        response = requests.get(url)
        return response.status_code == 200

    def _prepare_repo(self, repo_name):
        repo_url = f"https://github.com/{repo_name}.git"
        if not os.path.exists(self.repo_path):
            os.makedirs(os.path.dirname(self.repo_path), exist_ok=True)
            try:
                self.repo = Repo.clone_from(repo_url, self.repo_path)
            except GitCommandError as e:
                raise Exception(f"Cloning failed: {str(e)}")
        else:
            self.repo = Repo(self.repo_path)
            try:
                self.repo.remotes.origin.pull()
            except GitCommandError:
                raise Exception("Failed to sync with remote repository")

    def _sync_folder(self, src_folder):
        try:
            dest = os.path.join(self.repo_path, os.path.basename(src_folder))
            if self._files_changed(src_folder, dest):
                if os.path.exists(dest):
                    shutil.rmtree(dest)
                shutil.copytree(src_folder, dest, dirs_exist_ok=True)
        except Exception as e:
            raise Exception(f"Failed to sync {src_folder}: {str(e)}")

    def _files_changed(self, src, dest):
        if not os.path.exists(dest):
            return True
        src_hash = self._dir_hash(src)
        dest_hash = self._dir_hash(dest)
        return src_hash != dest_hash

    def _dir_hash(self, path):
        hash = hashlib.sha1()
        for root, dirs, files in os.walk(path):
            for name in files:
                filepath = os.path.join(root, name)
                with open(filepath, 'rb') as f:
                    while chunk := f.read(8192):
                        hash.update(chunk)
        return hash.hexdigest()

    def _git_commit_push(self):
        try:
            if self.repo.is_dirty() or len(self.repo.untracked_files) > 0:
                self.repo.git.add(A=True)
                self.repo.git.commit(m="AutoStash Backup")
                self.repo.remotes.origin.push()
        except GitCommandError as e:
            raise Exception(f"Git error: {str(e)}")

    def restore(self, repo_name):
        try:
            self.logger.info(f"Restoring from {repo_name}")
            repo_url = f"https://github.com/{repo_name}.git"
            restore_path = os.path.expanduser("~/autostash_restore")
            
            if os.path.exists(restore_path):
                shutil.rmtree(restore_path)
                
            Repo.clone_from(repo_url, restore_path)
            return restore_path
        except Exception as e:
            self.logger.error(f"Restore failed: {str(e)}")
            raise Exception(f"Restore failed: {str(e)}")

    def get_last_backup_time(self):
        try:
            with open(os.path.expanduser("~/.autostash/last_backup"), "r") as f:
                return f.read().strip()
        except:
            return None

