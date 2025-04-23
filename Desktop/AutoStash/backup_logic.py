import os
import shutil
import requests
import hashlib
from git import Repo, GitCommandError
from github import GithubException

class BackupManager:
    def __init__(self):
        self.repo_path = os.path.expanduser("~/.autostash_repo")
        self.repo = None

    def run(self, folders, repo_name):
        try:
            # Validate repo exists
            if not self._repo_exists(repo_name):
                raise Exception(f"Repository {repo_name} doesn't exist or you don't have access")

            # Clone or open repo
            self._prepare_repo(repo_name)
            
            # Sync files
            for folder in folders:
                self._sync_folder(folder)
            
            # Commit and push
            self._git_commit_push()
            
        except Exception as e:
            raise Exception(f"Backup failed: {str(e)}")

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
            
        # Compare directory hashes
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
            # Check if there are changes to commit
            if self.repo.is_dirty() or len(self.repo.untracked_files) > 0:
                self.repo.git.add(A=True)
                self.repo.git.commit(m="AutoStash Backup")
                # Always push (even if nothing new to commit)
                self.repo.remotes.origin.push()
        except GitCommandError as e:
            raise Exception(f"Git error: {str(e)}")

    def restore(self, repo_name):
        try:
            repo_url = f"https://github.com/{repo_name}.git"
            restore_path = os.path.expanduser("~/autostash_restore")
            
            if os.path.exists(restore_path):
                shutil.rmtree(restore_path)
                
            Repo.clone_from(repo_url, restore_path)
            return restore_path
        except Exception as e:
            raise Exception(f"Restore failed: {str(e)}")

