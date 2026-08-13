import time
import logging
from typing import Dict, Any, List, Optional
from src.config import settings

logger = logging.getLogger(__name__)

class GitHubService:
    """
    GitHub Integration Service to automatically create feature branches,
    commit code changes, and open Pull Requests.
    Includes mock fallback if GITHUB_TOKEN or GITHUB_REPO is not set.
    """

    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.repo_name = settings.GITHUB_REPO

    def is_configured(self) -> bool:
        return bool(self.token and self.repo_name and not self.token.startswith("ghp_123"))

    def create_pull_request(self, title: str, body: str, file_changes: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Creates a branch, commits changes, and opens a GitHub Pull Request.
        """
        branch_name = f"agentic/patch-{int(time.time())}"
        
        if not self.is_configured():
            repo_str = self.repo_name or "yusufansari563/agentic-ai-workflow"
            mock_pr_number = abs(hash(title)) % 900 + 100
            mock_pr_url = f"https://github.com/{repo_str}/pull/{mock_pr_number}"
            logger.info(f"[GitHub Service - Mock Mode] Simulated PR creation on {repo_str}: '{title}' -> {mock_pr_url}")
            return {
                "pr_number": mock_pr_number,
                "pr_url": mock_pr_url,
                "branch_name": branch_name,
                "repo": repo_str,
                "title": title,
                "status": "opened",
                "mode": "mock"
            }

        try:
            from github import Github
            g = Github(self.token)
            repo = g.get_repo(self.repo_name)
            default_branch = repo.default_branch
            
            # 1. Get SHA of default branch ref
            ref = repo.get_git_ref(f"heads/{default_branch}")
            sha = ref.object.sha
            
            # 2. Create new branch
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=sha)
            logger.info(f"[GitHub Service] Created new branch '{branch_name}' from '{default_branch}'.")
            
            # 3. Commit file changes if provided
            if file_changes:
                for change in file_changes:
                    file_path = change.get("path")
                    content = change.get("content", "")
                    commit_msg = change.get("commit_msg", f"Agentic updates to {file_path}")
                    try:
                        contents = repo.get_contents(file_path, ref=branch_name)
                        repo.update_file(contents.path, commit_msg, content, contents.sha, branch=branch_name)
                    except Exception:
                        repo.create_file(file_path, commit_msg, content, branch=branch_name)

            # 4. Open Pull Request
            pr = repo.create_pull(
                title=title,
                body=body,
                head=branch_name,
                base=default_branch
            )
            logger.info(f"[GitHub Service] Successfully opened PR #{pr.number}: {pr.html_url}")
            return {
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "branch_name": branch_name,
                "repo": self.repo_name,
                "title": title,
                "status": "opened",
                "mode": "live"
            }
        except Exception as e:
            logger.exception(f"[GitHub Service] Failed to create GitHub PR: {e}")
            repo_str = self.repo_name or "yusufansari563/agentic-ai-workflow"
            mock_pr_url = f"https://github.com/{repo_str}/pull/1"
            return {
                "pr_number": 1,
                "pr_url": mock_pr_url,
                "branch_name": branch_name,
                "repo": repo_str,
                "title": title,
                "status": "opened_fallback",
                "error": str(e),
                "mode": "fallback"
            }

# Global singleton
github_service = GitHubService()
