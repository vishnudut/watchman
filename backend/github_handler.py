import os
import json
import shutil
import tempfile
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from github import Github, GithubException
from git import Repo, GitCommandError
from dotenv import load_dotenv

load_dotenv()


class GitHubHandler:
    """
    Handles GitHub API interactions for Watchman security scanner
    Creates issues, comments, and manages repository interactions
    """

    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')

        if not self.token:
            raise ValueError("GITHUB_TOKEN not found in .env")

        try:
            self.github = Github(self.token)
            # Test the connection
            user = self.github.get_user()
            print(f"✓ GitHub API connected as: {user.login}")
        except GithubException as e:
            raise Exception(f"Failed to connect to GitHub API: {e}")

    def create_security_issue(
        self,
        repo_name: str,
        analysis_results: Dict,
        scan_metadata: Dict
    ) -> Dict:
        """
        Create a GitHub issue from security analysis results

        Args:
            repo_name: Repository name in format "owner/repo"
            analysis_results: Output from Claude AI analysis
            scan_metadata: Repository and scan context

        Returns:
            Dictionary with issue details and status
        """
        try:
            print(f"🔍 Creating security issue for {repo_name}")

            repo = self.github.get_repo(repo_name)

            # Generate issue title and body
            title = self._generate_issue_title(analysis_results)
            body = self._generate_issue_body(analysis_results, scan_metadata)

            # Create the issue
            issue = repo.create_issue(
                title=title,
                body=body,
                labels=["security", "watchman-scan", "needs-triage"]
            )

            print(f"✓ Created GitHub issue #{issue.number}")

            return {
                "success": True,
                "issue_number": issue.number,
                "issue_url": issue.html_url,
                "title": title,
                "created_at": issue.created_at.isoformat()
            }

        except GithubException as e:
            print(f"❌ Failed to create GitHub issue: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": getattr(e, 'status', None)
            }
        except Exception as e:
            print(f"❌ Unexpected error creating issue: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_issue_title(self, analysis_results: Dict) -> str:
        """Generate a descriptive title for the security issue"""
        critical_count = len(analysis_results.get('critical_issues', []))
        total_findings = len([
            item for sublist in analysis_results.get('by_severity', {}).values()
            for item in sublist
        ]) if 'by_severity' in analysis_results else critical_count

        if critical_count > 0:
            return f"🚨 Security Alert: {critical_count} Critical Issues Found ({total_findings} total findings)"
        else:
            return f"⚠️ Security Review: {total_findings} Security Issues Detected"

    def _generate_issue_body(self, analysis_results: Dict, scan_metadata: Dict) -> str:
        """Generate detailed issue body with findings and recommendations"""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        commit_sha = scan_metadata.get('commit_sha', 'unknown')[:8]
        branch = scan_metadata.get('branch', 'unknown')

        # Start with header
        body = f"""## 🔒 Watchman Security Scan Report

**Scan Date:** {timestamp}
**Branch:** `{branch}`
**Commit:** `{commit_sha}`
**Analyzer:** Claude AI + Semgrep

---

## 📋 Executive Summary

{analysis_results.get('executive_summary', 'Security analysis completed')}

"""

        # Add critical issues section
        critical_issues = analysis_results.get('critical_issues', [])
        if critical_issues:
            body += "## 🚨 Critical Issues\n\n"

            for i, issue in enumerate(critical_issues, 1):
                severity_emoji = self._get_severity_emoji(issue.get('severity', 'MEDIUM'))

                body += f"""### {i}. {severity_emoji} {issue.get('title', 'Security Issue')}

**File:** `{issue.get('file', 'unknown')}`
**Line:** {issue.get('line', 'N/A')}
**Severity:** {issue.get('severity', 'MEDIUM')}

**Description:**
{issue.get('description', 'Security vulnerability detected')}

**Business Impact:**
{issue.get('business_impact', 'Potential security risk')}

**Recommended Fix:**
```
{issue.get('recommended_fix', 'Review and remediate according to best practices')}
```

**Compliance Standards:**
{', '.join(issue.get('compliance_mapping', []))}

---

"""

        # Add recommended actions
        actions = analysis_results.get('recommended_actions', [])
        if actions:
            body += "## 🔧 Recommended Actions\n\n"
            for i, action in enumerate(actions, 1):
                body += f"{i}. {action}\n"
            body += "\n"

        # Add suggested tools
        tools = analysis_results.get('tools_to_use', [])
        if tools:
            body += "## 🛠️ Suggested Security Tools\n\n"
            for tool in tools:
                priority = tool.get('priority', 'N/A')
                tool_name = tool.get('tool', 'Unknown')
                body += f"- **{tool_name}** (Priority: {priority})\n"
            body += "\n"

        # Add footer
        body += """---

## 🤖 About This Report

This issue was automatically generated by [Watchman](https://github.com/your-org/watchman), an AI-powered security scanning platform that combines static analysis with intelligent remediation recommendations.

**Next Steps:**
1. Review each critical issue carefully
2. Implement the recommended fixes
3. Test your changes thoroughly
4. Re-run the security scan to verify fixes

**Questions?** Contact your DevSecOps team or create a discussion in this repository.

*Generated by Watchman v1.0 | Powered by Claude AI & Semgrep*
"""

        return body

    def _get_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level"""
        emoji_map = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🔵',
            'INFO': 'ℹ️'
        }
        return emoji_map.get(severity.upper(), '⚠️')

    def add_comment_to_issue(
        self,
        repo_name: str,
        issue_number: int,
        comment: str
    ) -> Dict:
        """
        Add a comment to an existing GitHub issue

        Args:
            repo_name: Repository name in format "owner/repo"
            issue_number: GitHub issue number
            comment: Comment text to add

        Returns:
            Dictionary with comment details and status
        """
        try:
            repo = self.github.get_repo(repo_name)
            issue = repo.get_issue(issue_number)

            comment_obj = issue.create_comment(comment)

            return {
                "success": True,
                "comment_id": comment_obj.id,
                "comment_url": comment_obj.html_url,
                "created_at": comment_obj.created_at.isoformat()
            }

        except GithubException as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": getattr(e, 'status', None)
            }

    def close_issue(
        self,
        repo_name: str,
        issue_number: int,
        reason: str = "completed"
    ) -> Dict:
        """
        Close a GitHub issue

        Args:
            repo_name: Repository name in format "owner/repo"
            issue_number: GitHub issue number
            reason: Reason for closing ("completed" or "not_planned")

        Returns:
            Dictionary with status
        """
        try:
            repo = self.github.get_repo(repo_name)
            issue = repo.get_issue(issue_number)

            # Add closing comment
            closing_comment = f"🔒 Security issues have been resolved. Issue closed by Watchman.\n\nReason: {reason}"
            issue.create_comment(closing_comment)

            # Close the issue
            issue.edit(state="closed")

            return {
                "success": True,
                "closed_at": datetime.now().isoformat(),
                "reason": reason
            }

        except GithubException as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_repository_info(self, repo_name: str) -> Dict:
        """
        Get basic repository information

        Args:
            repo_name: Repository name in format "owner/repo"

        Returns:
            Dictionary with repository details
        """
        try:
            repo = self.github.get_repo(repo_name)

            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "default_branch": repo.default_branch,
                "language": repo.language,
                "private": repo.private,
                "url": repo.html_url,
                "clone_url": repo.clone_url,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat()
            }

        except GithubException as e:
            return {
                "error": str(e),
                "error_code": getattr(e, 'status', None)
            }

    def list_open_security_issues(self, repo_name: str) -> List[Dict]:
        """
        List all open security issues created by Watchman

        Args:
            repo_name: Repository name in format "owner/repo"

        Returns:
            List of issue dictionaries
        """
        try:
            repo = self.github.get_repo(repo_name)
            issues = repo.get_issues(state="open", labels=["watchman-scan"])

            issue_list = []
            for issue in issues:
                issue_list.append({
                    "number": issue.number,
                    "title": issue.title,
                    "url": issue.html_url,
                    "created_at": issue.created_at.isoformat(),
                    "updated_at": issue.updated_at.isoformat(),
                    "labels": [label.name for label in issue.labels]
                })

            return issue_list

        except GithubException as e:
            print(f"❌ Failed to list issues: {e}")
            return []

    def clone_repository(
        self,
        repo_name: str,
        branch: str = "main",
        clone_path: Optional[str] = None
    ) -> Dict:
        """
        Clone a GitHub repository to local filesystem for scanning

        Args:
            repo_name: Repository name in format "owner/repo"
            branch: Git branch to clone (default: main)
            clone_path: Local path to clone to (optional, uses temp dir if not provided)

        Returns:
            Dictionary with clone status and local path
        """
        try:
            print(f"📥 Cloning repository: {repo_name} (branch: {branch})")

            # Get repository info first
            repo = self.github.get_repo(repo_name)
            clone_url = repo.clone_url

            # Determine local path
            if clone_path is None:
                temp_dir = tempfile.mkdtemp(prefix="watchman_clone_")
                local_path = Path(temp_dir) / repo.name
            else:
                local_path = Path(clone_path)
                local_path.parent.mkdir(parents=True, exist_ok=True)

            # Remove existing directory if it exists
            if local_path.exists():
                shutil.rmtree(local_path)

            # Clone the repository
            cloned_repo = Repo.clone_from(
                clone_url,
                local_path,
                branch=branch,
                depth=1  # Shallow clone for faster operation
            )

            # Get commit information
            commit = cloned_repo.head.commit
            commit_sha = commit.hexsha
            commit_message = commit.message.strip()

            print(f"✓ Repository cloned successfully to: {local_path}")
            print(f"✓ Latest commit: {commit_sha[:8]} - {commit_message}")

            return {
                "success": True,
                "local_path": str(local_path),
                "clone_url": clone_url,
                "branch": branch,
                "commit_sha": commit_sha,
                "commit_message": commit_message,
                "repo_info": {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "language": repo.language,
                    "private": repo.private
                }
            }

        except GitCommandError as e:
            print(f"❌ Git clone failed: {e}")
            return {
                "success": False,
                "error": f"Git error: {e}",
                "error_type": "git_error"
            }
        except GithubException as e:
            print(f"❌ GitHub API error: {e}")
            return {
                "success": False,
                "error": f"GitHub API error: {e}",
                "error_type": "github_api_error"
            }
        except Exception as e:
            print(f"❌ Unexpected error during clone: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected_error"
            }

    def cleanup_clone(self, local_path: str) -> bool:
        """
        Clean up cloned repository directory

        Args:
            local_path: Path to cloned repository

        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
                print(f"🧹 Cleaned up cloned repository: {local_path}")
                return True
            return True
        except Exception as e:
            print(f"⚠️ Failed to cleanup {local_path}: {e}")
            return False

    def clone_scan_and_cleanup(
        self,
        repo_name: str,
        scanner,
        branch: str = "main"
    ) -> Dict:
        """
        Complete workflow: clone repository, scan it, and cleanup

        Args:
            repo_name: Repository name in format "owner/repo"
            scanner: SecurityScanner instance
            branch: Git branch to scan

        Returns:
            Dictionary with scan results and metadata
        """
        clone_result = self.clone_repository(repo_name, branch)

        if not clone_result["success"]:
            return {
                "success": False,
                "error": "Failed to clone repository",
                "clone_error": clone_result["error"]
            }

        local_path = clone_result["local_path"]

        try:
            # Run security scan
            print(f"🔍 Starting security scan on cloned repository...")
            scan_results = scanner.scan_repository(local_path)

            # Add repository metadata to scan results
            scan_results["repo_metadata"] = {
                "repo_name": repo_name,
                "branch": branch,
                "commit_sha": clone_result["commit_sha"],
                "commit_message": clone_result["commit_message"],
                "local_path": local_path
            }

            return {
                "success": True,
                "scan_results": scan_results,
                "clone_metadata": clone_result
            }

        except Exception as e:
            print(f"❌ Error during scan: {e}")
            return {
                "success": False,
                "error": f"Scan failed: {e}",
                "clone_metadata": clone_result
            }

        finally:
            # Always cleanup, even if scan fails
            self.cleanup_clone(local_path)


if __name__ == "__main__":
    # Test the GitHub handler
    try:
        handler = GitHubHandler()

        # Mock analysis results for testing
        test_analysis = {
            "executive_summary": "Critical SQL injection vulnerability discovered requiring immediate attention",
            "critical_issues": [
                {
                    "title": "SQL Injection in User Authentication",
                    "severity": "CRITICAL",
                    "file": "app/auth.py",
                    "line": 45,
                    "description": "User input directly concatenated into SQL query without parameterization",
                    "business_impact": "Complete database compromise possible",
                    "recommended_fix": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
                    "compliance_mapping": ["OWASP Top 10", "SOC 2"]
                }
            ],
            "recommended_actions": [
                "Implement parameterized queries immediately",
                "Review all database interactions",
                "Add input validation middleware"
            ],
            "tools_to_use": [
                {"tool": "Bandit", "priority": 1}
            ]
        }

        test_metadata = {
            "repo_name": "test-security-app",
            "branch": "main",
            "commit_sha": "abc123def456789"
        }

        print("GitHub Handler Test Results:")
        print("=" * 50)

        # Test repository info (if repo exists)
        # Uncomment and modify with a real repo name to test
        # repo_info = handler.get_repository_info("octocat/Hello-World")
        # print(f"Repository Info: {json.dumps(repo_info, indent=2)}")

        # Test cloning functionality (uncomment to test with a real repo)
        # print("\n" + "="*50)
        # print("TESTING REPOSITORY CLONING")
        # print("="*50)
        # clone_result = handler.clone_repository("octocat/Hello-World")
        # if clone_result["success"]:
        #     print(f"✓ Clone successful: {clone_result['local_path']}")
        #     handler.cleanup_clone(clone_result['local_path'])
        # else:
        #     print(f"❌ Clone failed: {clone_result['error']}")

        print("✓ GitHub Handler initialized successfully")
        print("✓ Ready to create security issues and clone repositories")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
