import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class EmailHandler:
    """
    Handles email notifications for Watchman security scanner
    Sends notifications for security issues, PR creation, and scan results
    """

    def __init__(self):
        """Initialize email handler with SMTP configuration"""
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')  # App password for Gmail
        self.sender_name = os.getenv('SENDER_NAME', 'Watchman Security Scanner')

        # Notification recipients
        self.default_recipients = self._parse_recipients(os.getenv('NOTIFICATION_RECIPIENTS', ''))
        self.admin_recipients = self._parse_recipients(os.getenv('ADMIN_RECIPIENTS', ''))

        # Validate configuration
        if not self.sender_email or not self.sender_password:
            raise ValueError("SENDER_EMAIL and SENDER_PASSWORD must be set in .env file")

        print(f"✓ Email handler initialized - SMTP: {self.smtp_server}:{self.smtp_port}")
        print(f"✓ Sender: {self.sender_name} <{self.sender_email}>")
        print(f"✓ Default recipients: {len(self.default_recipients)}")

        # Test connection
        self._test_connection()

    def _parse_recipients(self, recipients_str: str) -> List[str]:
        """Parse comma-separated email addresses"""
        if not recipients_str:
            return []
        return [email.strip() for email in recipients_str.split(',') if email.strip()]

    def _test_connection(self):
        """Test SMTP connection"""
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
            print("✓ SMTP connection test successful")
        except Exception as e:
            print(f"⚠️ SMTP connection test failed: {e}")
            print("  Make sure your email credentials are correct in .env")

    def send_security_issue_notification(
        self,
        repo_name: str,
        issue_details: Dict,
        analysis_results: Dict,
        scan_metadata: Dict,
        recipients: Optional[List[str]] = None
    ) -> Dict:
        """
        Send notification when a security issue is created

        Args:
            repo_name: Repository name
            issue_details: GitHub issue creation results
            analysis_results: AI analysis results
            scan_metadata: Scan context and metadata
            recipients: Email recipients (uses defaults if not provided)

        Returns:
            Dictionary with email sending results
        """
        try:
            print(f"📧 Sending security issue notification for {repo_name}")

            recipients = recipients or self.default_recipients
            if not recipients:
                return {"success": False, "error": "No recipients configured"}

            # Generate email content
            subject = f"🚨 Security Alert: New vulnerabilities found in {repo_name}"
            html_content = self._generate_security_issue_email(
                repo_name, issue_details, analysis_results, scan_metadata
            )

            # Send email
            result = self._send_email(
                recipients=recipients,
                subject=subject,
                html_content=html_content,
                email_type="security_issue"
            )

            if result["success"]:
                print(f"✓ Security issue notification sent to {len(recipients)} recipients")

            return result

        except Exception as e:
            print(f"❌ Failed to send security issue notification: {e}")
            return {"success": False, "error": str(e)}

    def send_pr_created_notification(
        self,
        repo_name: str,
        pr_details: Dict,
        code_fixes: Dict,
        scan_metadata: Dict,
        recipients: Optional[List[str]] = None
    ) -> Dict:
        """
        Send notification when an automated security fix PR is created

        Args:
            repo_name: Repository name
            pr_details: Pull request creation results
            code_fixes: AI-generated code fixes
            scan_metadata: Scan context and metadata
            recipients: Email recipients (uses defaults if not provided)

        Returns:
            Dictionary with email sending results
        """
        try:
            print(f"📧 Sending PR creation notification for {repo_name}")

            recipients = recipients or self.default_recipients
            if not recipients:
                return {"success": False, "error": "No recipients configured"}

            # Generate email content
            subject = f"🔧 Automated Fix: Security PR created for {repo_name}"
            html_content = self._generate_pr_created_email(
                repo_name, pr_details, code_fixes, scan_metadata
            )

            # Send email
            result = self._send_email(
                recipients=recipients,
                subject=subject,
                html_content=html_content,
                email_type="pr_created"
            )

            if result["success"]:
                print(f"✓ PR creation notification sent to {len(recipients)} recipients")

            return result

        except Exception as e:
            print(f"❌ Failed to send PR notification: {e}")
            return {"success": False, "error": str(e)}

    def send_scan_summary_notification(
        self,
        repo_name: str,
        workflow_results: Dict,
        recipients: Optional[List[str]] = None
    ) -> Dict:
        """
        Send scan summary notification with complete workflow results

        Args:
            repo_name: Repository name
            workflow_results: Complete workflow results
            recipients: Email recipients (uses defaults if not provided)

        Returns:
            Dictionary with email sending results
        """
        try:
            print(f"📧 Sending scan summary notification for {repo_name}")

            recipients = recipients or self.default_recipients
            if not recipients:
                return {"success": False, "error": "No recipients configured"}

            # Generate email content
            findings = workflow_results.get("findings", {})
            total_findings = findings.get("total", 0)

            if total_findings > 0:
                subject = f"📊 Security Scan Complete: {total_findings} issues found in {repo_name}"
            else:
                subject = f"✅ Security Scan Complete: No issues found in {repo_name}"

            html_content = self._generate_scan_summary_email(repo_name, workflow_results)

            # Send email
            result = self._send_email(
                recipients=recipients,
                subject=subject,
                html_content=html_content,
                email_type="scan_summary"
            )

            if result["success"]:
                print(f"✓ Scan summary notification sent to {len(recipients)} recipients")

            return result

        except Exception as e:
            print(f"❌ Failed to send scan summary notification: {e}")
            return {"success": False, "error": str(e)}

    def _send_email(
        self,
        recipients: List[str],
        subject: str,
        html_content: str,
        email_type: str = "notification"
    ) -> Dict:
        """Send email via SMTP"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = ", ".join(recipients)

            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipients, message.as_string())

            return {
                "success": True,
                "recipients": recipients,
                "subject": subject,
                "email_type": email_type,
                "sent_at": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ SMTP send error: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipients": recipients,
                "email_type": email_type
            }

    def _generate_security_issue_email(
        self,
        repo_name: str,
        issue_details: Dict,
        analysis_results: Dict,
        scan_metadata: Dict
    ) -> str:
        """Generate HTML email for security issue notification"""

        issue_url = issue_details.get("issue_url", "#")
        issue_number = issue_details.get("issue_number", "N/A")
        critical_issues = analysis_results.get("critical_issues", [])
        executive_summary = analysis_results.get("executive_summary", "Security vulnerabilities detected")

        # Build critical issues list
        issues_html = ""
        for i, issue in enumerate(critical_issues[:5], 1):  # Top 5 issues
            severity = issue.get("severity", "UNKNOWN")
            title = issue.get("title", "Security Issue")
            file_path = issue.get("file", "unknown")
            line = issue.get("line", "")

            severity_color = {
                "CRITICAL": "#dc2626",
                "HIGH": "#ea580c",
                "MEDIUM": "#ca8a04",
                "LOW": "#16a34a"
            }.get(severity, "#6b7280")

            issues_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">
                    <span style="background: {severity_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                        {severity}
                    </span>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-weight: 500;">{title}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-family: monospace; font-size: 13px;">
                    {file_path}{':' + str(line) if line else ''}
                </td>
            </tr>"""

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Security Alert - {repo_name}</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #374151; margin: 0; padding: 0; background-color: #f9fafb;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">

                <!-- Header -->
                <div style="text-align: center; padding: 20px 0; border-bottom: 2px solid #dc2626;">
                    <h1 style="color: #dc2626; margin: 0; font-size: 24px;">
                        🚨 Security Alert
                    </h1>
                    <p style="color: #6b7280; margin: 5px 0 0 0;">Watchman Security Scanner</p>
                </div>

                <!-- Summary -->
                <div style="padding: 20px 0;">
                    <h2 style="color: #1f2937; margin: 0 0 10px 0;">Security Vulnerabilities Detected</h2>
                    <p style="margin: 0 0 15px 0;">
                        <strong>Repository:</strong> {repo_name}<br>
                        <strong>Branch:</strong> {scan_metadata.get('branch', 'unknown')}<br>
                        <strong>Scan Time:</strong> {scan_metadata.get('scan_timestamp', 'unknown')}
                    </p>
                    <p style="background: #fef3c7; padding: 15px; border-radius: 6px; border-left: 4px solid #f59e0b; margin: 15px 0;">
                        <strong>Executive Summary:</strong><br>
                        {executive_summary}
                    </p>
                </div>

                <!-- Critical Issues -->
                <div style="padding: 20px 0;">
                    <h3 style="color: #1f2937; margin: 0 0 15px 0;">Critical Security Issues</h3>
                    <table style="width: 100%; border-collapse: collapse; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden;">
                        <thead>
                            <tr style="background: #f9fafb;">
                                <th style="padding: 12px 8px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #e5e7eb;">Severity</th>
                                <th style="padding: 12px 8px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #e5e7eb;">Issue</th>
                                <th style="padding: 12px 8px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #e5e7eb;">Location</th>
                            </tr>
                        </thead>
                        <tbody>
                            {issues_html}
                        </tbody>
                    </table>
                </div>

                <!-- Action Required -->
                <div style="background: #fef2f2; padding: 20px; border-radius: 6px; border-left: 4px solid #dc2626; margin: 20px 0;">
                    <h3 style="color: #dc2626; margin: 0 0 10px 0;">⚡ Action Required</h3>
                    <p style="margin: 0 0 15px 0;">
                        A GitHub issue has been automatically created to track these security vulnerabilities.
                        Please review and address these issues promptly to maintain your application's security.
                    </p>
                    <a href="{issue_url}"
                       style="display: inline-block; background: #dc2626; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: 500;">
                        View GitHub Issue #{issue_number}
                    </a>
                </div>

                <!-- Footer -->
                <div style="text-align: center; padding: 20px 0; border-top: 1px solid #e5e7eb; margin-top: 30px; color: #6b7280; font-size: 14px;">
                    <p style="margin: 0;">
                        This notification was automatically generated by<br>
                        <strong>Watchman Security Scanner</strong> 🛡️
                    </p>
                    <p style="margin: 10px 0 0 0; font-size: 12px;">
                        Scan ID: {scan_metadata.get('scan_run_id', 'N/A')} |
                        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        return html_template

    def _generate_pr_created_email(
        self,
        repo_name: str,
        pr_details: Dict,
        code_fixes: Dict,
        scan_metadata: Dict
    ) -> str:
        """Generate HTML email for PR creation notification"""

        pr_url = pr_details.get("pr_url", "#")
        pr_number = pr_details.get("pr_number", "N/A")
        branch_name = pr_details.get("branch_name", "unknown")
        files_changed = pr_details.get("files_changed", [])
        summary = code_fixes.get("summary", "Security fixes applied")

        # Build files changed list
        files_html = ""
        for file_path in files_changed[:10]:  # Show up to 10 files
            files_html += f"""
            <li style="padding: 5px 0; font-family: monospace; font-size: 13px; color: #374151;">
                📄 {file_path}
            </li>"""

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Automated Security Fix - {repo_name}</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #374151; margin: 0; padding: 0; background-color: #f9fafb;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">

                <!-- Header -->
                <div style="text-align: center; padding: 20px 0; border-bottom: 2px solid #16a34a;">
                    <h1 style="color: #16a34a; margin: 0; font-size: 24px;">
                        🔧 Automated Security Fix
                    </h1>
                    <p style="color: #6b7280; margin: 5px 0 0 0;">Watchman Security Scanner</p>
                </div>

                <!-- Summary -->
                <div style="padding: 20px 0;">
                    <h2 style="color: #1f2937; margin: 0 0 10px 0;">Security Fix Pull Request Created</h2>
                    <p style="margin: 0 0 15px 0;">
                        <strong>Repository:</strong> {repo_name}<br>
                        <strong>Branch:</strong> {branch_name}<br>
                        <strong>Files Modified:</strong> {len(files_changed)}
                    </p>
                    <p style="background: #dcfce7; padding: 15px; border-radius: 6px; border-left: 4px solid #16a34a; margin: 15px 0;">
                        <strong>Fixes Applied:</strong><br>
                        {summary}
                    </p>
                </div>

                <!-- Files Changed -->
                <div style="padding: 20px 0;">
                    <h3 style="color: #1f2937; margin: 0 0 15px 0;">Files Modified</h3>
                    <ul style="list-style: none; padding: 0; margin: 0; background: #f9fafb; border-radius: 6px; padding: 15px;">
                        {files_html}
                    </ul>
                </div>

                <!-- Action Required -->
                <div style="background: #eff6ff; padding: 20px; border-radius: 6px; border-left: 4px solid #3b82f6; margin: 20px 0;">
                    <h3 style="color: #3b82f6; margin: 0 0 10px 0;">🔍 Review Required</h3>
                    <p style="margin: 0 0 15px 0;">
                        An automated security fix pull request has been created. Please review the changes carefully
                        and test thoroughly before merging to ensure functionality remains intact.
                    </p>
                    <a href="{pr_url}"
                       style="display: inline-block; background: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: 500;">
                        Review Pull Request #{pr_number}
                    </a>
                </div>

                <!-- Security Note -->
                <div style="background: #fefce8; padding: 15px; border-radius: 6px; border-left: 4px solid #eab308; margin: 20px 0; font-size: 14px;">
                    <strong>⚠️ Important:</strong> While these fixes are AI-generated and designed to address security vulnerabilities,
                    please verify that all functionality works as expected after applying the changes.
                </div>

                <!-- Footer -->
                <div style="text-align: center; padding: 20px 0; border-top: 1px solid #e5e7eb; margin-top: 30px; color: #6b7280; font-size: 14px;">
                    <p style="margin: 0;">
                        This pull request was automatically generated by<br>
                        <strong>Watchman Security Scanner</strong> 🛡️
                    </p>
                    <p style="margin: 10px 0 0 0; font-size: 12px;">
                        Scan ID: {scan_metadata.get('scan_run_id', 'N/A')} |
                        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        return html_template

    def _generate_scan_summary_email(self, repo_name: str, workflow_results: Dict) -> str:
        """Generate HTML email for scan summary notification"""

        findings = workflow_results.get("findings", {})
        total_findings = findings.get("total", 0)
        critical_count = findings.get("critical", 0)
        warnings_count = findings.get("warnings", 0)
        info_count = findings.get("info", 0)
        duration = workflow_results.get("duration_seconds", 0)

        github_issue = workflow_results.get("github_issue", {})
        security_pr = workflow_results.get("security_fix_pr", {})

        # Determine scan status
        if total_findings == 0:
            status_color = "#16a34a"
            status_icon = "✅"
            status_text = "Clean"
        elif critical_count > 0:
            status_color = "#dc2626"
            status_icon = "🚨"
            status_text = "Critical Issues Found"
        else:
            status_color = "#ea580c"
            status_icon = "⚠️"
            status_text = "Issues Found"

        # Build actions section
        actions_html = ""
        if github_issue.get("success"):
            actions_html += f"""
            <p style="margin: 5px 0;">
                📋 <strong>GitHub Issue:</strong>
                <a href="{github_issue.get('issue_url', '#')}" style="color: #3b82f6; text-decoration: none;">
                    Issue #{github_issue.get('issue_number', 'N/A')}
                </a>
            </p>"""

        if security_pr.get("success"):
            actions_html += f"""
            <p style="margin: 5px 0;">
                🔧 <strong>Automated Fix PR:</strong>
                <a href="{security_pr.get('pr_url', '#')}" style="color: #16a34a; text-decoration: none;">
                    PR #{security_pr.get('pr_number', 'N/A')}
                </a>
            </p>"""

        if not actions_html:
            actions_html = "<p style='margin: 5px 0; color: #6b7280;'>No actions taken (no significant issues found)</p>"

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Security Scan Summary - {repo_name}</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #374151; margin: 0; padding: 0; background-color: #f9fafb;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">

                <!-- Header -->
                <div style="text-align: center; padding: 20px 0; border-bottom: 2px solid {status_color};">
                    <h1 style="color: {status_color}; margin: 0; font-size: 24px;">
                        {status_icon} Scan Complete
                    </h1>
                    <p style="color: #6b7280; margin: 5px 0 0 0;">Watchman Security Scanner</p>
                </div>

                <!-- Summary -->
                <div style="padding: 20px 0;">
                    <h2 style="color: #1f2937; margin: 0 0 10px 0;">{status_text}</h2>
                    <p style="margin: 0 0 15px 0;">
                        <strong>Repository:</strong> {repo_name}<br>
                        <strong>Branch:</strong> {workflow_results.get('branch', 'unknown')}<br>
                        <strong>Scan Duration:</strong> {duration:.1f} seconds<br>
                        <strong>Completed:</strong> {workflow_results.get('completed_at', 'unknown')}
                    </p>
                </div>

                <!-- Findings Summary -->
                <div style="padding: 20px 0;">
                    <h3 style="color: #1f2937; margin: 0 0 15px 0;">Security Findings</h3>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                        <div style="text-align: center; padding: 15px; background: #fef2f2; border-radius: 6px; border: 1px solid #fecaca;">
                            <div style="font-size: 24px; font-weight: bold; color: #dc2626;">{critical_count}</div>
                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase; font-weight: 500;">Critical</div>
                        </div>
                        <div style="text-align: center; padding: 15px; background: #fef3c7; border-radius: 6px; border: 1px solid #fde68a;">
                            <div style="font-size: 24px; font-weight: bold; color: #ea580c;">{warnings_count}</div>
                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase; font-weight: 500;">Warnings</div>
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 15px; padding: 10px; background: #f9fafb; border-radius: 6px;">
                        <strong>Total Issues Found: {total_findings}</strong>
                    </div>
                </div>

                <!-- Actions Taken -->
                <div style="padding: 20px 0;">
                    <h3 style="color: #1f2937; margin: 0 0 15px 0;">Actions Taken</h3>
                    <div style="background: #f9fafb; padding: 15px; border-radius: 6px; border-left: 4px solid #6b7280;">
                        {actions_html}
                    </div>
                </div>

                <!-- Next Steps -->
                {f'''
                <div style="background: #fef3c7; padding: 20px; border-radius: 6px; border-left: 4px solid #f59e0b; margin: 20px 0;">
                    <h3 style="color: #92400e; margin: 0 0 10px 0;">📋 Next Steps</h3>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>Review all security findings in the GitHub issue</li>
                        {f"<li>Test and review the automated fix PR before merging</li>" if security_pr.get("success") else ""}
                        <li>Address any remaining security vulnerabilities</li>
                        <li>Run additional security tests if needed</li>
                    </ul>
                </div>
                ''' if total_findings > 0 else f'''
                <div style="background: #dcfce7; padding: 20px; border-radius: 6px; border-left: 4px solid #16a34a; margin: 20px 0;">
                    <h3 style="color: #166534; margin: 0 0 10px 0;">🎉 Great Job!</h3>
                    <p style="margin: 0;">No security vulnerabilities were found in this scan. Your code is looking secure!</p>
                </div>
                '''}

                <!-- Footer -->
                <div style="text-align: center; padding: 20px 0; border-top: 1px solid #e5e7eb; margin-top: 30px; color: #6b7280; font-size: 14px;">
                    <p style="margin: 0;">
                        This scan summary was automatically generated by<br>
                        <strong>Watchman Security Scanner</strong> 🛡️
                    </p>
                    <p style="margin: 10px 0 0 0; font-size: 12px;">
                        Workflow ID: {workflow_results.get('workflow_id', 'N/A')} |
                        Scan ID: {workflow_results.get('scan_run_id', 'N/A')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        return html_template


if __name__ == "__main__":
    # Test the email handler
    try:
        print("🧪 Testing Email Handler")
        print("=" * 50)

        # Initialize email handler
        email_handler = EmailHandler()

        # Test data
        test_repo = "example/test-repo"
        test_issue = {
            "success": True,
            "issue_number": 123,
            "issue_url": "https://github.com/example/test-repo/issues/123"
        }
        test_analysis = {
            "executive_summary": "Found 2 critical security vulnerabilities requiring immediate attention",
            "critical_issues": [
                {
                    "title": "SQL Injection Vulnerability",
                    "severity": "CRITICAL",
                    "file": "app.py",
                    "line": 45,
                    "description": "User input directly concatenated in SQL query"
                },
                {
                    "title": "Hardcoded API Key",
                    "severity": "HIGH",
                    "file": "config.py",
                    "line": 12,
                    "description": "API key hardcoded in source code"
                }
            ]
        }
        test_metadata = {
            "branch": "main",
            "scan_timestamp": datetime.now().isoformat(),
            "scan_run_id": "test_123"
        }

        # Test email generation (without sending)
        print("📧 Testing email generation...")

        # Generate security issue email
        security_email = email_handler._generate_security_issue_email(
            test_repo, test_issue, test_analysis, test_metadata
        )
        print("✓ Security issue email generated")

        # Generate PR creation email
        test_pr = {
            "success": True,
            "pr_number": 456,
            "pr_url": "https://github.com/example/test-repo/pull/456",
            "branch_name": "security-fixes-20241215",
            "files_changed": ["app.py", "config.py", ".env.example"]
        }
        test_fixes = {
            "summary": "Fix SQL injection and hardcoded secrets vulnerabilities",
            "file_changes": [
                {"file_path": "app.py", "issue_type": "sql-injection"},
                {"file_path": "config.py", "issue_type": "hardcoded-secrets"}
            ]
        }

        pr_email = email_handler._generate_pr_created_email(
            test_repo, test_pr, test_fixes, test_metadata
        )
        print("✓ PR creation email generated")

        # Generate scan summary email
        test_workflow = {
            "findings": {"total": 2, "critical": 1, "warnings": 1, "info": 0},
            "duration_seconds": 45.2,
            "branch": "main",
            "completed_at": datetime.now().isoformat(),
            "workflow_id": "scan_test_123",
            "scan_run_id": "test_123",
            "github_issue": test_issue,
            "security_fix_pr": test_pr
        }

        summary_email = email_handler._generate_scan_summary_email(test_repo, test_workflow)
        print("✓ Scan summary email generated")

        print("\n✅ All email templates generated successfully!")
        print("✅ Email handler test complete!")

        # Save test emails to files for review
        with open("test_security_email.html", "w") as f:
            f.write(security_email)
        with open("test_pr_email.html", "w") as f:
            f.write(pr_email)
        with open("test_summary_email.html", "w") as f:
            f.write(summary_email)

        print("\n💾 Test emails saved:")
        print("   - test_security_email.html")
        print("   - test_pr_email.html")
        print("   - test_summary_email.html")

    except Exception as e:
        print(f"❌ Email handler test failed: {e}")
        import traceback
        traceback.print_exc()
