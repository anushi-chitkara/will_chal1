import os
from github import Github, GithubException

class GitHubManager:
    def __init__(self):
        self.token = None
        self.gh = None
    
    def authenticate(self, token):
        self.token = token
        self.gh = Github(token)
        self._configure_git_credentials(token)
    
    def get_repos(self):
        if not self.gh:
            raise Exception("Not authenticated!")
        return [f"{repo.owner.login}/{repo.name}" for repo in self.gh.get_user().get_repos()]
    
    def _configure_git_credentials(self, token):
        """Store GitHub token to avoid terminal prompts"""
        import subprocess
        # Store token in git credential helper
        subprocess.run(["git", "config", "--global", "credential.helper", "store"])
        # Create credentials file with token
        with open(os.path.expanduser("~/.git-credentials"), "w") as f:
            f.write(f"https://{token}:x-oauth-basic@github.com\n")
        # Secure the file
        os.chmod(os.path.expanduser("~/.git-credentials"), 0o600)

