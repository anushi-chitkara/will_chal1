from github import Github, GithubException

class GitHubManager:
    def __init__(self):
        self.token = None
        self.gh = None
    
    def authenticate(self, token):
        self.token = token
        self.gh = Github(token)
    
    def get_repos(self):
        if not self.gh:
            raise Exception("Not authenticated!")
        return [f"{repo.owner.login}/{repo.name}" for repo in self.gh.get_user().get_repos()]

