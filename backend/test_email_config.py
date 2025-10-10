#!/usr/bin/env python3
"""
Email Configuration Test Script for Watchman Security Scanner
Tests email settings and sends test notifications to verify setup
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from email_handler import EmailHandler


def test_email_configuration():
    """Test basic email configuration and connection"""
    print("🧪 Testing Email Configuration")
    print("=" * 50)

    try:
        # Initialize email handler (will test SMTP connection)
        email_handler = EmailHandler()

        print("✅ Email handler initialized successfully")
        print(f"📧 SMTP Server: {email_handler.smtp_server}:{email_handler.smtp_port}")
        print(f"👤 Sender: {email_handler.sender_name} <{email_handler.sender_email}>")
        print(f"📫 Default Recipients: {len(email_handler.default_recipients)}")

        if email_handler.default_recipients:
            print(f"   Recipients: {', '.join(email_handler.default_recipients)}")
        else:
            print("   ⚠️ No default recipients configured!")

        return email_handler

    except Exception as e:
        print(f"❌ Email configuration test failed: {e}")
        print("\n🔧 Configuration Help:")
        print("1. Copy .env.email.example to your .env file")
        print("2. Set SENDER_EMAIL to your email address")
        print("3. Set SENDER_PASSWORD to your app password")
        print("4. Set NOTIFICATION_RECIPIENTS to test email addresses")
        print("5. For Gmail: Enable 2FA and generate an app password")
        return None


def test_send_notifications():
    """Test sending actual email notifications"""
    print("\n🧪 Testing Email Notifications")
    print("=" * 50)

    try:
        email_handler = EmailHandler()

        if not email_handler.default_recipients:
            print("❌ Cannot test email sending - no recipients configured")
            print("   Add NOTIFICATION_RECIPIENTS to your .env file")
            return False

        print(f"📧 Testing email sending to: {', '.join(email_handler.default_recipients)}")

        # Test data
        test_repo = "example/test-security-repo"

        # Test 1: Security Issue Notification
        print("\n📋 Testing security issue notification...")
        test_issue = {
            "success": True,
            "issue_number": 123,
            "issue_url": "https://github.com/example/test-security-repo/issues/123",
            "title": "Critical Security Vulnerabilities Found",
            "created_at": datetime.now().isoformat()
        }

        test_analysis = {
            "executive_summary": "Found 2 critical security vulnerabilities including SQL injection and hardcoded credentials that require immediate attention.",
            "critical_issues": [
                {
                    "title": "SQL Injection Vulnerability",
                    "severity": "CRITICAL",
                    "file": "src/database.py",
                    "line": 45,
                    "description": "User input directly concatenated into SQL query without sanitization",
                    "business_impact": "Attackers could read, modify, or delete database data",
                    "recommended_fix": "Use parameterized queries with prepared statements"
                },
                {
                    "title": "Hardcoded Database Password",
                    "severity": "CRITICAL",
                    "file": "config/database.py",
                    "line": 12,
                    "description": "Database password hardcoded in source code",
                    "business_impact": "Database credentials exposed to anyone with code access",
                    "recommended_fix": "Move password to environment variables"
                }
            ],
            "recommended_actions": [
                "Fix SQL injection by implementing parameterized queries",
                "Move hardcoded credentials to environment variables",
                "Run additional security scan after fixes"
            ]
        }

        test_metadata = {
            "repo_name": test_repo,
            "branch": "main",
            "commit_sha": "abc123def456",
            "scan_timestamp": datetime.now().isoformat(),
            "scan_run_id": "test_001"
        }

        issue_result = email_handler.send_security_issue_notification(
            repo_name=test_repo,
            issue_details=test_issue,
            analysis_results=test_analysis,
            scan_metadata=test_metadata
        )

        if issue_result.get("success"):
            print("✅ Security issue notification sent successfully!")
        else:
            print(f"❌ Failed to send security issue notification: {issue_result.get('error')}")

        # Test 2: PR Creation Notification
        print("\n🔧 Testing PR creation notification...")
        test_pr = {
            "success": True,
            "pr_number": 456,
            "pr_url": "https://github.com/example/test-security-repo/pull/456",
            "branch_name": "security-fixes-20241215-143022",
            "title": "🔒 Security: Fix SQL injection and hardcoded credentials",
            "files_changed": ["src/database.py", "config/database.py", ".env.example"],
            "created_at": datetime.now().isoformat()
        }

        test_fixes = {
            "summary": "Applied automated fixes for SQL injection vulnerability and hardcoded database credentials",
            "commit_message": "security: fix SQL injection and move credentials to env vars",
            "file_changes": [
                {
                    "file_path": "src/database.py",
                    "issue_type": "sql-injection",
                    "description": "Replace string concatenation with parameterized queries",
                    "changes": [
                        {
                            "line_start": 45,
                            "line_end": 45,
                            "old_code": "query = \"SELECT * FROM users WHERE id = '\" + user_id + \"'\"",
                            "new_code": "query = \"SELECT * FROM users WHERE id = %s\"\ncursor.execute(query, (user_id,))",
                            "explanation": "Use parameterized query to prevent SQL injection"
                        }
                    ]
                },
                {
                    "file_path": "config/database.py",
                    "issue_type": "hardcoded-secrets",
                    "description": "Move database password to environment variables",
                    "changes": [
                        {
                            "line_start": 12,
                            "line_end": 12,
                            "old_code": "DB_PASSWORD = 'hardcoded_secret_123'",
                            "new_code": "DB_PASSWORD = os.environ.get('DB_PASSWORD')",
                            "explanation": "Load password from environment variable for security"
                        }
                    ]
                }
            ],
            "additional_files": [
                {
                    "file_path": ".env.example",
                    "content": "# Database Configuration\nDB_PASSWORD=your-secure-password-here\n",
                    "purpose": "Template for environment variables"
                }
            ]
        }

        pr_result = email_handler.send_pr_created_notification(
            repo_name=test_repo,
            pr_details=test_pr,
            code_fixes=test_fixes,
            scan_metadata=test_metadata
        )

        if pr_result.get("success"):
            print("✅ PR creation notification sent successfully!")
        else:
            print(f"❌ Failed to send PR notification: {pr_result.get('error')}")

        # Test 3: Scan Summary Notification
        print("\n📊 Testing scan summary notification...")
        test_workflow = {
            "success": True,
            "workflow_id": "scan_test_001",
            "scan_run_id": "test_001",
            "repo_name": test_repo,
            "branch": "main",
            "commit_sha": "abc123def456",
            "duration_seconds": 47.3,
            "findings": {
                "total": 3,
                "critical": 2,
                "warnings": 1,
                "info": 0
            },
            "github_issue": test_issue,
            "security_fix_pr": test_pr,
            "analysis_summary": "Critical security vulnerabilities found and automated fixes created",
            "completed_at": datetime.now().isoformat()
        }

        summary_result = email_handler.send_scan_summary_notification(
            repo_name=test_repo,
            workflow_results=test_workflow
        )

        if summary_result.get("success"):
            print("✅ Scan summary notification sent successfully!")
        else:
            print(f"❌ Failed to send scan summary: {summary_result.get('error')}")

        # Summary
        success_count = sum([
            1 if issue_result.get("success") else 0,
            1 if pr_result.get("success") else 0,
            1 if summary_result.get("success") else 0
        ])

        print(f"\n📊 Test Results: {success_count}/3 email types sent successfully")

        return success_count == 3

    except Exception as e:
        print(f"❌ Email notification test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_email_templates():
    """Test email template generation without sending"""
    print("\n🧪 Testing Email Template Generation")
    print("=" * 50)

    try:
        email_handler = EmailHandler()

        # Test template generation
        test_repo = "example/template-test"

        # Mock data for templates
        mock_issue = {
            "success": True,
            "issue_number": 999,
            "issue_url": "https://github.com/example/template-test/issues/999"
        }

        mock_analysis = {
            "executive_summary": "Template test - multiple security issues found",
            "critical_issues": [
                {
                    "title": "Cross-Site Scripting (XSS)",
                    "severity": "HIGH",
                    "file": "templates/user.html",
                    "line": 23,
                    "description": "User input rendered without escaping"
                }
            ]
        }

        mock_metadata = {
            "repo_name": test_repo,
            "branch": "develop",
            "scan_timestamp": datetime.now().isoformat(),
            "scan_run_id": "template_test"
        }

        # Generate templates
        print("📧 Generating security issue email template...")
        security_html = email_handler._generate_security_issue_email(
            test_repo, mock_issue, mock_analysis, mock_metadata
        )

        print("🔧 Generating PR creation email template...")
        mock_pr = {
            "pr_number": 888,
            "pr_url": "https://github.com/example/template-test/pull/888",
            "branch_name": "security-fixes-template",
            "files_changed": ["templates/user.html"]
        }

        mock_fixes = {
            "summary": "Fix XSS vulnerability in user templates",
            "file_changes": [{"file_path": "templates/user.html", "issue_type": "xss"}]
        }

        pr_html = email_handler._generate_pr_created_email(
            test_repo, mock_pr, mock_fixes, mock_metadata
        )

        print("📊 Generating scan summary email template...")
        mock_workflow = {
            "findings": {"total": 1, "critical": 0, "warnings": 1, "info": 0},
            "duration_seconds": 32.1,
            "branch": "develop",
            "completed_at": datetime.now().isoformat(),
            "workflow_id": "template_test",
            "scan_run_id": "template_test",
            "github_issue": mock_issue,
            "security_fix_pr": mock_pr
        }

        summary_html = email_handler._generate_scan_summary_email(test_repo, mock_workflow)

        # Save template files
        template_files = [
            ("test_security_issue_template.html", security_html),
            ("test_pr_creation_template.html", pr_html),
            ("test_scan_summary_template.html", summary_html)
        ]

        for filename, content in template_files:
            with open(filename, 'w') as f:
                f.write(content)
            print(f"💾 Saved: {filename}")

        print(f"\n✅ All {len(template_files)} email templates generated successfully!")
        print("🌐 Open the HTML files in your browser to preview the emails")

        return True

    except Exception as e:
        print(f"❌ Email template test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def display_configuration_help():
    """Display helpful configuration information"""
    print("\n" + "=" * 60)
    print("📧 EMAIL SETUP HELP")
    print("=" * 60)

    print("\n🔧 Required Environment Variables:")
    print("   SENDER_EMAIL=your-email@gmail.com")
    print("   SENDER_PASSWORD=your-app-password")
    print("   NOTIFICATION_RECIPIENTS=recipient1@company.com,recipient2@company.com")

    print("\n📧 Gmail Setup (Recommended):")
    print("   1. Go to https://myaccount.google.com/security")
    print("   2. Enable 2-factor authentication")
    print("   3. Go to 'App passwords' section")
    print("   4. Generate new app password for 'Mail'")
    print("   5. Use Gmail address for SENDER_EMAIL")
    print("   6. Use app password (not your regular password) for SENDER_PASSWORD")

    print("\n🧪 Testing:")
    print("   python test_email_config.py")
    print("   Check your inbox for test emails")

    print("\n⚠️ Troubleshooting:")
    print("   - Make sure 2FA is enabled on Gmail")
    print("   - Use app password, not regular password")
    print("   - Check spam folder for test emails")
    print("   - Verify recipient email addresses are correct")


if __name__ == "__main__":
    print("🚀 Watchman Email Configuration Tests")
    print("=" * 70)

    # Display help information
    display_configuration_help()

    # Test 1: Basic configuration
    email_handler = test_email_configuration()

    if not email_handler:
        print("\n❌ Email configuration failed - stopping tests")
        sys.exit(1)

    # Test 2: Template generation (safe, no sending)
    template_success = test_email_templates()

    # Test 3: Actual email sending (optional)
    print("\n" + "=" * 50)
    send_test = input("Do you want to send test emails to configured recipients? (y/N): ")

    if send_test.lower() in ['y', 'yes']:
        if not email_handler.default_recipients:
            print("❌ Cannot send test emails - no recipients configured")
            print("   Add NOTIFICATION_RECIPIENTS to your .env file")
        else:
            print(f"\n📧 Sending test emails to: {', '.join(email_handler.default_recipients)}")
            sending_success = test_send_notifications()

            if sending_success:
                print("\n🎉 All email tests passed! Check your inbox.")
            else:
                print("\n⚠️ Some email tests failed. Check the error messages above.")
    else:
        print("\n✅ Email configuration and templates tested successfully!")
        print("   Templates saved as HTML files for preview")

    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Email Configuration: {'PASSED' if email_handler else 'FAILED'}")
    print(f"✅ Template Generation: {'PASSED' if template_success else 'FAILED'}")

    if 'sending_success' in locals():
        print(f"✅ Email Sending: {'PASSED' if sending_success else 'FAILED'}")
    else:
        print("⏭️  Email Sending: SKIPPED (user choice)")

    print("\n🎯 Next Steps:")
    print("1. Review generated HTML email templates")
    print("2. Test with actual email recipients")
    print("3. Integrate into main Watchman workflow")
    print("4. Configure notification preferences")
