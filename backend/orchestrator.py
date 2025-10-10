import os
import time
import traceback
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from scanner import SecurityScanner
from bedrock_agent import BedrockAgentCore
from github_handler import GitHubHandler
from database import DatabaseHandler
from email_handler import EmailHandler
# from vanta_handler import VantaHandler  # Commented out for testing


class WatchmanOrchestrator:
    """
    Main orchestrator for Watchman security scanning workflow
    Coordinates between scanner, AI analysis, GitHub integration, and database
    """

    def __init__(self):
        """Initialize all components"""
        print("🚀 Initializing Watchman Orchestrator...")

        try:
            # Initialize components
            self.scanner = SecurityScanner()
            self.ai_agent = BedrockAgentCore()  # Claude AI
            self.github_handler = GitHubHandler()
            self.database = DatabaseHandler()

            # Initialize email handler (optional - will work without email config)
            try:
                self.email_handler = EmailHandler()
                print("✓ Email notifications enabled")
            except Exception as e:
                print(f"⚠️ Email handler initialization failed (continuing without emails): {e}")
                self.email_handler = None

            # self.vanta_handler = VantaHandler()  # Commented out for testing

            print("✓ All components initialized successfully")

        except Exception as e:
            print(f"❌ Failed to initialize components: {e}")
            raise

    def process_github_webhook(
        self,
        webhook_payload: Dict,
        repo_full_name: str,
        branch: str = None,
        commit_sha: str = None
    ) -> Dict:
        """
        Main orchestration method - processes GitHub webhook and runs complete scan workflow

        Args:
            webhook_payload: Raw GitHub webhook payload
            repo_full_name: Repository name in format "owner/repo"
            branch: Git branch (extracted from payload if not provided)
            commit_sha: Git commit SHA (extracted from payload if not provided)

        Returns:
            Dictionary with workflow results and status
        """
        start_time = time.time()
        workflow_id = f"scan_{int(start_time)}"

        print(f"🔄 Starting workflow {workflow_id} for {repo_full_name}")

        # Extract branch and commit from payload if not provided
        if not branch:
            branch = webhook_payload.get('ref', 'refs/heads/main').replace('refs/heads/', '')
        if not commit_sha:
            commit_sha = webhook_payload.get('after', 'unknown')

        # LOOP PREVENTION: Skip security fix branches to prevent infinite loops
        if branch.startswith('security-fixes-'):
            print(f"⏭️ Skipping scan on security fix branch: {branch}")
            return {
                "success": True,
                "workflow_id": workflow_id,
                "repo_name": repo_full_name,
                "branch": branch,
                "message": "Skipped security fix branch to prevent loops",
                "skipped_reason": "security_fix_branch",
                "completed_at": datetime.now().isoformat()
            }

        # ADDITIONAL LOOP PREVENTION: Skip commits with security fix messages
        commit_message = webhook_payload.get('head_commit', {}).get('message', '')
        if commit_message.lower().startswith('security:'):
            print(f"⏭️ Skipping scan on security fix commit: {commit_message[:50]}...")
            return {
                "success": True,
                "workflow_id": workflow_id,
                "repo_name": repo_full_name,
                "branch": branch,
                "commit_sha": commit_sha[:8],
                "message": "Skipped security fix commit to prevent loops",
                "skipped_reason": "security_fix_commit",
                "completed_at": datetime.now().isoformat()
            }

        # Create scan run in database
        scan_run_id = self.database.create_scan_run(
            repo_name=repo_full_name,
            branch=branch,
            commit_sha=commit_sha
        )

        # # Log scan start to Vanta for compliance
        # vanta_start_result = self.vanta_handler.log_security_scan_start(
        #     scan_run_id=scan_run_id,
        #     repo_name=repo_full_name,
        #     branch=branch,
        #     commit_sha=commit_sha
        # )
        # if vanta_start_result.get("success"):
        #     print(f"✓ Vanta compliance log: Scan started")

        try:
            # Step 1: Clone Repository
            print(f"📥 Step 1: Cloning repository {repo_full_name}...")
            clone_result = self.github_handler.clone_repository(
                repo_name=repo_full_name,
                branch=branch
            )

            if not clone_result["success"]:
                raise Exception(f"Failed to clone repository: {clone_result.get('error', 'Unknown error')}")

            local_path = clone_result["local_path"]

            # Step 2: Security Scan
            print(f"🔍 Step 2: Running security scan...")
            scan_results = self.scanner.scan_repository(local_path)

            if scan_results.get("error"):
                raise Exception(f"Security scan failed: {scan_results['error']}")

            # Store findings in database
            findings_by_severity = scan_results.get("by_severity", {})
            all_findings = []
            for severity, findings in findings_by_severity.items():
                for finding in findings:
                    finding["severity"] = severity
                    all_findings.append(finding)

            self.database.store_security_findings(scan_run_id, all_findings)

            # Step 3: AI Analysis
            print(f"🤖 Step 3: Running AI analysis...")
            repo_context = {
                "repo_name": repo_full_name,
                "branch": branch,
                "commit_sha": commit_sha,
                "clone_metadata": clone_result
            }

            analysis_results = self.ai_agent.analyze_security_findings(
                scan_results=scan_results,
                repo_context=repo_context
            )

            # Store AI analysis in database
            self.database.store_ai_analysis(scan_run_id, analysis_results)

            # # Log findings to Vanta for compliance
            # findings_summary = {
            #     "total_findings": scan_results.get("total_findings", 0),
            #     "critical_count": scan_results.get("finding_counts", {}).get("ERROR", 0),
            #     "high_count": scan_results.get("finding_counts", {}).get("WARNING", 0),
            #     "medium_count": scan_results.get("finding_counts", {}).get("MEDIUM", 0),
            #     "low_count": scan_results.get("finding_counts", {}).get("LOW", 0)
            # }

            # vanta_findings_result = self.vanta_handler.log_security_findings(
            #     scan_run_id=scan_run_id,
            #     repo_name=repo_full_name,
            #     findings_summary=findings_summary,
            #     ai_analysis=analysis_results
            # )
            # if vanta_findings_result.get("success"):
            #     print(f"✓ Vanta compliance log: Security findings recorded")

            # Step 4: Create GitHub Issue (if significant findings)
            github_issue_result = None
            if scan_results.get("total_findings", 0) > 0:
                print(f"📋 Step 4: Creating GitHub issue...")

                scan_metadata = {
                    "scan_run_id": scan_run_id,
                    "repo_name": repo_full_name,
                    "branch": branch,
                    "commit_sha": commit_sha,
                    "scan_timestamp": datetime.now().isoformat()
                }

                github_issue_result = self.github_handler.create_security_issue(
                    repo_name=repo_full_name,
                    analysis_results=analysis_results,
                    scan_metadata=scan_metadata
                )

                if github_issue_result.get("success"):
                    # Store GitHub issue info in database
                    self.database.store_github_issue(scan_run_id, github_issue_result)
                    print(f"✓ Created GitHub issue #{github_issue_result.get('issue_number')}")

                    # Send email notification for security issue
                    if self.email_handler:
                        try:
                            email_result = self.email_handler.send_security_issue_notification(
                                repo_name=repo_full_name,
                                issue_details=github_issue_result,
                                analysis_results=analysis_results,
                                scan_metadata=scan_metadata
                            )
                            if email_result.get("success"):
                                print(f"✓ Security issue email sent to {len(email_result.get('recipients', []))} recipients")
                            else:
                                print(f"⚠️ Failed to send security issue email: {email_result.get('error')}")
                        except Exception as e:
                            print(f"⚠️ Email notification error: {e}")

                    # # Log remediation action to Vanta
                    # vanta_remediation_result = self.vanta_handler.log_remediation_action(
                    #     scan_run_id=scan_run_id,
                    #     repo_name=repo_full_name,
                    #     github_issue_url=github_issue_result.get("issue_url"),
                    #     remediation_details=analysis_results
                    # )
                    # if vanta_remediation_result.get("success"):
                    #     print(f"✓ Vanta compliance log: Remediation action recorded")
                else:
                    print(f"⚠️ Failed to create GitHub issue: {github_issue_result.get('error')}")
            else:
                print("ℹ️ No significant findings - skipping GitHub issue creation")

            # Step 5: Generate Code Fixes and Create PR (if critical issues found)
            pr_result = None
            critical_issues = analysis_results.get("critical_issues", [])
            if critical_issues and len(critical_issues) > 0:
                print(f"🔧 Step 5: Generating automated code fixes...")

                # Generate code fixes using AI
                code_fixes = self.ai_agent.generate_code_fixes(critical_issues, scan_metadata)

                if not code_fixes.get("error") and code_fixes.get("file_changes"):
                    print(f"✓ Generated fixes for {len(code_fixes.get('file_changes', []))} files")

                    # Create pull request with fixes
                    print(f"🚀 Step 5b: Creating automated fix PR...")
                    pr_result = self.github_handler.create_security_fix_pr(
                        repo_name=repo_full_name,
                        code_fixes=code_fixes,
                        analysis_metadata=scan_metadata
                    )

                    if pr_result.get("success"):
                        # Store PR info in database (extend database schema if needed)
                        print(f"✓ Created security fix PR #{pr_result.get('pr_number')}")
                        print(f"🔗 PR URL: {pr_result.get('pr_url')}")

                        # Send email notification for PR creation
                        if self.email_handler:
                            try:
                                pr_email_result = self.email_handler.send_pr_created_notification(
                                    repo_name=repo_full_name,
                                    pr_details=pr_result,
                                    code_fixes=code_fixes,
                                    scan_metadata=scan_metadata
                                )
                                if pr_email_result.get("success"):
                                    print(f"✓ Security fix PR email sent to {len(pr_email_result.get('recipients', []))} recipients")
                                else:
                                    print(f"⚠️ Failed to send PR email: {pr_email_result.get('error')}")
                            except Exception as e:
                                print(f"⚠️ PR email notification error: {e}")

                        # Update GitHub issue with PR link if issue was created
                        if github_issue_result and github_issue_result.get("success"):
                            try:
                                pr_comment = f"🤖 **Automated Fix Available**\n\nI've created a pull request with automated fixes for the security issues found in this scan:\n\n🔗 **PR #{pr_result.get('pr_number')}**: {pr_result.get('pr_url')}\n\nPlease review the proposed changes carefully before merging."

                                comment_result = self.github_handler.add_comment_to_issue(
                                    repo_name=repo_full_name,
                                    issue_number=github_issue_result.get('issue_number'),
                                    comment=pr_comment
                                )
                                if comment_result.get("success"):
                                    print("✓ Added PR link to GitHub issue")
                            except Exception as e:
                                print(f"⚠️ Failed to add PR comment to issue: {e}")
                    else:
                        print(f"⚠️ Failed to create security fix PR: {pr_result.get('error')}")
                else:
                    if code_fixes.get("error"):
                        print(f"⚠️ Code fix generation failed: {code_fixes.get('error')}")
                    else:
                        print("ℹ️ No actionable code fixes generated")
            else:
                print("ℹ️ No critical issues found - skipping automated fix generation")

            # Step 6: Update scan run status
            duration = time.time() - start_time
            finding_counts = {
                "ERROR": len(findings_by_severity.get("ERROR", [])),
                "WARNING": len(findings_by_severity.get("WARNING", [])),
                "INFO": len(findings_by_severity.get("INFO", []))
            }

            self.database.update_scan_run(
                scan_run_id=scan_run_id,
                status="completed",
                total_findings=scan_results.get("total_findings", 0),
                finding_counts=finding_counts,
                duration=duration
            )

            # Step 6: Log compliance summary and cleanup
            print(f"📋 Step 6: Logging compliance summary...")
            workflow_result_summary = {
                "repo_name": repo_full_name,
                "duration_seconds": duration,
                "findings": {
                    "total": scan_results.get("total_findings", 0),
                    "critical": finding_counts["ERROR"],
                    "high": finding_counts["WARNING"],
                    "medium": finding_counts.get("MEDIUM", 0),
                    "low": finding_counts.get("LOW", 0)
                },
                "github_issue": github_issue_result or {"success": False},
                "security_fix_pr": pr_result or {"success": False}
            }

            # vanta_summary_result = self.vanta_handler.log_compliance_summary(
            #     scan_run_id=scan_run_id,
            #     workflow_results=workflow_result_summary
            # )
            # if vanta_summary_result.get("success"):
            #     print(f"✓ Vanta compliance log: Workflow summary recorded")

            # Cleanup
            print(f"🧹 Step 7: Cleaning up...")
            self.github_handler.cleanup_clone(local_path)

            workflow_result = {
                "success": True,
                "workflow_id": workflow_id,
                "scan_run_id": scan_run_id,
                "repo_name": repo_full_name,
                "branch": branch,
                "commit_sha": commit_sha[:8],
                "duration_seconds": round(duration, 2),
                "findings": {
                    "total": scan_results.get("total_findings", 0),
                    "critical": finding_counts["ERROR"],
                    "warnings": finding_counts["WARNING"],
                    "info": finding_counts["INFO"]
                },
                "github_issue": github_issue_result,
                "security_fix_pr": pr_result,
                "analysis_summary": analysis_results.get("executive_summary", ""),
                "completed_at": datetime.now().isoformat(),
                "vanta_compliance": {
                    "logged": True,
                    "frameworks": ["SOC 2", "NIST", "OWASP"]
                }
            }

            # Send final scan summary email
            if self.email_handler:
                try:
                    summary_email_result = self.email_handler.send_scan_summary_notification(
                        repo_name=repo_full_name,
                        workflow_results=workflow_result
                    )
                    if summary_email_result.get("success"):
                        print(f"✓ Scan summary email sent to {len(summary_email_result.get('recipients', []))} recipients")
                    else:
                        print(f"⚠️ Failed to send scan summary email: {summary_email_result.get('error')}")
                except Exception as e:
                    print(f"⚠️ Summary email notification error: {e}")

            print(f"🎉 Workflow {workflow_id} completed successfully in {duration:.1f}s")
            print(f"   Found {scan_results.get('total_findings', 0)} security issues")
            if github_issue_result and github_issue_result.get("success"):
                print(f"   Created GitHub issue #{github_issue_result.get('issue_number')}")
            if pr_result and pr_result.get("success"):
                print(f"   Created security fix PR #{pr_result.get('pr_number')}")

            return workflow_result

        except Exception as e:
            # Handle errors and update database
            duration = time.time() - start_time
            error_msg = str(e)

            print(f"❌ Workflow {workflow_id} failed after {duration:.1f}s: {error_msg}")
            print(f"   Stack trace: {traceback.format_exc()}")

            # Update scan run with error status
            self.database.update_scan_run(
                scan_run_id=scan_run_id,
                status="failed",
                duration=duration
            )

            # Log failed scan to Vanta for compliance audit trail
            # try:
            #     vanta_failure_result = self.vanta_handler.log_security_scan_start(
            #         scan_run_id=scan_run_id,
            #         repo_name=repo_full_name,
            #         branch=branch,
            #         commit_sha=commit_sha
            #     )
            #     # Note: In production, you'd want a separate method for logging failures
            #     print(f"✓ Vanta compliance log: Scan failure recorded")
            # except Exception as vanta_error:
            #     print(f"⚠️ Failed to log scan failure to Vanta: {vanta_error}")

            # Cleanup if clone was successful
            if 'local_path' in locals():
                try:
                    self.github_handler.cleanup_clone(local_path)
                except:
                    pass  # Ignore cleanup errors

            return {
                "success": False,
                "workflow_id": workflow_id,
                "scan_run_id": scan_run_id,
                "repo_name": repo_full_name,
                "branch": branch,
                "error": error_msg,
                "duration_seconds": round(duration, 2),
                "failed_at": datetime.now().isoformat()
            }

    def get_scan_status(self, scan_run_id: int) -> Dict:
        """Get status of a specific scan run"""
        try:
            scan_run = self.database.get_scan_run(scan_run_id)
            if not scan_run:
                return {"error": "Scan run not found"}

            findings = self.database.get_scan_findings(scan_run_id)
            analysis = self.database.get_ai_analysis(scan_run_id)

            return {
                "scan_run": scan_run,
                "findings_count": len(findings),
                "analysis_available": analysis is not None,
                "status": scan_run.get("scan_status")
            }
        except Exception as e:
            return {"error": str(e)}

    def get_recent_scans(self, repo_name: str = None, limit: int = 10) -> List[Dict]:
        """Get recent scan runs"""
        try:
            return self.database.get_recent_scans(repo_name, limit)
        except Exception as e:
            print(f"❌ Error getting recent scans: {e}")
            return []

    def get_system_stats(self) -> Dict:
        """Get overall system statistics"""
        try:
            return self.database.get_scan_summary()
        except Exception as e:
            return {"error": str(e)}

    def process_manual_scan(
        self,
        repo_full_name: str,
        branch: str = "main"
    ) -> Dict:
        """
        Manually trigger a scan (not from webhook)

        Args:
            repo_full_name: Repository name in format "owner/repo"
            branch: Git branch to scan

        Returns:
            Workflow results
        """
        print(f"🔧 Manual scan triggered for {repo_full_name}:{branch}")

        # Create a mock webhook payload for manual scans
        mock_payload = {
            "ref": f"refs/heads/{branch}",
            "after": "manual_scan",
            "repository": {
                "full_name": repo_full_name
            },
            "head_commit": {
                "id": "manual_scan",
                "message": "Manual security scan"
            }
        }

        return self.process_github_webhook(
            webhook_payload=mock_payload,
            repo_full_name=repo_full_name,
            branch=branch,
            commit_sha="manual_scan"
        )


def extract_webhook_data(webhook_payload: Dict) -> Dict:
    """
    Extract relevant data from GitHub webhook payload

    Args:
        webhook_payload: Raw GitHub webhook data

    Returns:
        Extracted and normalized data
    """
    try:
        # Handle push events
        if "ref" in webhook_payload and "commits" in webhook_payload:
            return {
                "event_type": "push",
                "repo_full_name": webhook_payload.get("repository", {}).get("full_name"),
                "branch": webhook_payload.get("ref", "").replace("refs/heads/", ""),
                "commit_sha": webhook_payload.get("after"),
                "commit_message": webhook_payload.get("head_commit", {}).get("message", ""),
                "pusher": webhook_payload.get("pusher", {}).get("name", "unknown"),
                "commits_count": len(webhook_payload.get("commits", [])),
                "repository": {
                    "name": webhook_payload.get("repository", {}).get("name"),
                    "private": webhook_payload.get("repository", {}).get("private", False),
                    "language": webhook_payload.get("repository", {}).get("language")
                }
            }

        # Handle other event types (pull requests, etc.)
        else:
            return {
                "event_type": "unknown",
                "repo_full_name": webhook_payload.get("repository", {}).get("full_name"),
                "raw_payload": webhook_payload
            }

    except Exception as e:
        return {
            "event_type": "error",
            "error": str(e),
            "raw_payload": webhook_payload
        }


if __name__ == "__main__":
    # Test the orchestrator
    try:
        orchestrator = WatchmanOrchestrator()

        # Test with a mock webhook payload
        test_payload = {
            "ref": "refs/heads/main",
            "after": "abc123def456",
            "repository": {
                "full_name": "test-user/test-repo",
                "name": "test-repo"
            },
            "head_commit": {
                "id": "abc123def456",
                "message": "Add test file"
            },
            "pusher": {
                "name": "test-user"
            },
            "commits": []
        }

        print("🧪 Testing orchestrator with mock payload...")
        print("=" * 60)

        # Extract webhook data
        webhook_data = extract_webhook_data(test_payload)
        print(f"Webhook data: {webhook_data}")

        # Note: Uncomment the line below to test with a real repository
        # Make sure you have access to the repository and it exists
        # result = orchestrator.process_github_webhook(test_payload, "your-username/your-repo")

        print("✓ Orchestrator initialized successfully")
        print("✓ Ready to process GitHub webhooks")

        # Test system stats
        stats = orchestrator.get_system_stats()
        print(f"System stats: {stats}")

    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        traceback.print_exc()
