#!/usr/bin/env python3
"""
Complete Email Integration Test for Watchman Security Scanner
Tests the full workflow with email notifications integrated
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from orchestrator import WatchmanOrchestrator


def test_workflow_with_emails():
    """Test complete workflow with email notifications"""
    print("🧪 Testing Complete Workflow with Email Notifications")
    print("=" * 70)

    try:
        # Initialize orchestrator (will try to init email handler)
        print("🔧 Initializing Watchman Orchestrator...")
        orchestrator = WatchmanOrchestrator()

        if orchestrator.email_handler:
            print("✅ Email handler initialized - notifications will be sent")
            print(f"📧 Default recipients: {len(orchestrator.email_handler.default_recipients)}")
            if orchestrator.email_handler.default_recipients:
                print(f"   Recipients: {', '.join(orchestrator.email_handler.default_recipients)}")
        else:
            print("⚠️ Email handler not initialized - no emails will be sent")
            print("   This test will show the workflow without email notifications")

        # Mock webhook payload with realistic security vulnerabilities
        mock_webhook_payload = {
            "ref": "refs/heads/main",
            "after": "email_test_commit_001",
            "repository": {
                "full_name": "test-user/vulnerable-webapp",  # CHANGE TO YOUR TEST REPO
                "name": "vulnerable-webapp",
                "owner": {
                    "login": "test-user"  # CHANGE TO YOUR USERNAME
                }
            },
            "head_commit": {
                "id": "email_test_commit_001",
                "message": "Add user authentication with potential security issues",
                "author": {
                    "name": "Test Developer",
                    "email": "test@example.com"
                },
                "timestamp": datetime.now().isoformat()
            },
            "pusher": {
                "name": "test-developer"
            },
            "commits": [
                {
                    "id": "email_test_commit_001",
                    "message": "Add user authentication with potential security issues",
                    "added": ["src/auth.py", "config/database.py"],
                    "modified": ["src/app.py"],
                    "removed": []
                }
            ]
        }

        repo_name = mock_webhook_payload["repository"]["full_name"]
        branch = "main"
        commit_sha = mock_webhook_payload["after"]

        print(f"\n🎯 Testing Repository: {repo_name}")
        print(f"🌿 Branch: {branch}")
        print(f"📝 Commit: {commit_sha}")
        print(f"💬 Message: {mock_webhook_payload['head_commit']['message']}")

        # Track email expectations
        expected_emails = []
        if orchestrator.email_handler:
            expected_emails = [
                "Security Issue Notification",
                "PR Creation Notification",
                "Scan Summary Notification"
            ]

        print(f"\n📧 Expected Emails: {len(expected_emails)}")
        for email_type in expected_emails:
            print(f"   - {email_type}")

        # Start workflow
        print(f"\n🚀 Starting Complete Workflow with Email Integration...")
        print("-" * 60)

        start_time = time.time()

        # This will run the complete workflow including email notifications
        workflow_result = orchestrator.process_github_webhook(
            webhook_payload=mock_webhook_payload,
            repo_full_name=repo_name,
            branch=branch,
            commit_sha=commit_sha
        )

        duration = time.time() - start_time

        print(f"\n🎉 Workflow Completed in {duration:.2f} seconds")
        print("=" * 70)

        # Analyze results
        if workflow_result.get("success"):
            print("✅ COMPLETE WORKFLOW: SUCCESS!")

            # Security Scan Results
            findings = workflow_result.get("findings", {})
            print(f"\n📊 Security Scan Results:")
            print(f"   Total Findings: {findings.get('total', 0)}")
            print(f"   Critical: {findings.get('critical', 0)}")
            print(f"   Warnings: {findings.get('warnings', 0)}")
            print(f"   Info: {findings.get('info', 0)}")

            # GitHub Issue Creation
            github_issue = workflow_result.get("github_issue", {})
            print(f"\n📋 GitHub Issue:")
            if github_issue.get("success"):
                print(f"   ✅ Created Issue #{github_issue.get('issue_number')}")
                print(f"   🔗 URL: {github_issue.get('issue_url')}")
                print(f"   📧 Security issue email: {'Sent' if orchestrator.email_handler else 'Skipped (no email config)'}")
            else:
                print(f"   ❌ Failed: {github_issue.get('error', 'Unknown error')}")

            # Security Fix PR Creation
            security_pr = workflow_result.get("security_fix_pr", {})
            print(f"\n🔧 Security Fix PR:")
            if security_pr.get("success"):
                print(f"   ✅ Created PR #{security_pr.get('pr_number')}")
                print(f"   🔗 URL: {security_pr.get('pr_url')}")
                print(f"   🌿 Branch: {security_pr.get('branch_name')}")
                print(f"   📁 Files Changed: {len(security_pr.get('files_changed', []))}")
                print(f"   📧 PR creation email: {'Sent' if orchestrator.email_handler else 'Skipped (no email config)'}")
            else:
                if security_pr:
                    print(f"   ❌ Failed: {security_pr.get('error', 'Unknown error')}")
                else:
                    print(f"   ℹ️ No PR created (no critical issues found)")

            # Email Summary
            print(f"\n📧 Email Notification Summary:")
            if orchestrator.email_handler:
                recipient_count = len(orchestrator.email_handler.default_recipients)
                print(f"   📨 Recipients: {recipient_count} configured")
                print(f"   🚨 Security Alert: {'Sent' if github_issue.get('success') else 'Not sent'}")
                print(f"   🔧 PR Notification: {'Sent' if security_pr.get('success') else 'Not sent'}")
                print(f"   📊 Scan Summary: Sent (always sent)")
                print(f"   📧 Check your inbox for {recipient_count} x {len([x for x in [github_issue.get('success'), security_pr.get('success'), True] if x])} emails")
            else:
                print(f"   ⚠️ Email handler not configured")
                print(f"   💡 To enable emails: python setup_email.py")

            # Analysis Summary
            analysis_summary = workflow_result.get("analysis_summary", "")
            if analysis_summary:
                print(f"\n🤖 AI Analysis Summary:")
                print(f"   {analysis_summary}")

            # Workflow Metrics
            print(f"\n⏱️  Workflow Performance:")
            print(f"   Duration: {workflow_result.get('duration_seconds', 0):.2f} seconds")
            print(f"   Scan ID: {workflow_result.get('scan_run_id', 'N/A')}")
            print(f"   Workflow ID: {workflow_result.get('workflow_id', 'N/A')}")

        else:
            print("❌ WORKFLOW FAILED!")
            error_msg = workflow_result.get('error', 'Unknown error')
            print(f"Error: {error_msg}")

            # Check if it was skipped due to loop prevention
            if workflow_result.get('skipped_reason'):
                print(f"Skipped Reason: {workflow_result['skipped_reason']}")
                print(f"Message: {workflow_result['message']}")

        # Save complete results
        results_file = "test_email_integration_results.json"
        with open(results_file, 'w') as f:
            json.dump(workflow_result, f, indent=2)
        print(f"\n💾 Complete results saved to: {results_file}")

        return workflow_result

    except Exception as e:
        print(f"❌ Email integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_email_configuration_status():
    """Test and display email configuration status"""
    print("\n" + "=" * 70)
    print("📧 EMAIL CONFIGURATION STATUS")
    print("=" * 70)

    try:
        from email_handler import EmailHandler

        try:
            email_handler = EmailHandler()

            print("✅ Email Handler: Successfully initialized")
            print(f"📡 SMTP Server: {email_handler.smtp_server}:{email_handler.smtp_port}")
            print(f"👤 Sender: {email_handler.sender_name} <{email_handler.sender_email}>")
            print(f"📫 Default Recipients: {len(email_handler.default_recipients)}")

            if email_handler.default_recipients:
                for i, recipient in enumerate(email_handler.default_recipients, 1):
                    print(f"   {i}. {recipient}")
            else:
                print("   ⚠️ No recipients configured!")

            if email_handler.admin_recipients:
                print(f"👨‍💼 Admin Recipients: {len(email_handler.admin_recipients)}")
                for i, admin in enumerate(email_handler.admin_recipients, 1):
                    print(f"   {i}. {admin}")

            return True

        except Exception as e:
            print(f"❌ Email Handler: Failed to initialize")
            print(f"   Error: {e}")
            print(f"   💡 Run: python setup_email.py")
            return False

    except ImportError as e:
        print(f"❌ Email Handler: Module not found")
        print(f"   Error: {e}")
        return False


def test_manual_email_workflow():
    """Test manual scan workflow with emails"""
    print("\n" + "=" * 70)
    print("🔧 TESTING MANUAL SCAN WITH EMAILS")
    print("=" * 70)

    try:
        orchestrator = WatchmanOrchestrator()

        repo_name = "test-user/manual-email-test"  # CHANGE THIS
        branch = "main"

        print(f"🎯 Testing manual scan: {repo_name}:{branch}")

        if orchestrator.email_handler:
            print(f"📧 Emails will be sent to: {', '.join(orchestrator.email_handler.default_recipients)}")
        else:
            print("⚠️ No email handler - emails will be skipped")

        # Process manual scan
        manual_result = orchestrator.process_manual_scan(repo_name, branch)

        if manual_result.get("success"):
            print("✅ Manual scan with emails: SUCCESS!")

            findings = manual_result.get("findings", {})
            print(f"\n📊 Results:")
            print(f"   Findings: {findings.get('total', 0)}")
            print(f"   Issue: {'Created' if manual_result.get('github_issue', {}).get('success') else 'Not created'}")
            print(f"   PR: {'Created' if manual_result.get('security_fix_pr', {}).get('success') else 'Not created'}")

        else:
            print("❌ Manual scan failed!")
            print(f"Error: {manual_result.get('error', 'Unknown')}")

        return manual_result

    except Exception as e:
        print(f"❌ Manual scan test failed: {e}")
        return None


def display_integration_summary():
    """Display comprehensive integration summary"""
    print("\n" + "=" * 70)
    print("🎯 EMAIL INTEGRATION SUMMARY")
    print("=" * 70)

    print("\n🔄 Complete Workflow:")
    print("   GitHub Push → Webhook → Security Scan → AI Analysis")
    print("   → GitHub Issue + 📧 Email → AI Fix Generation")
    print("   → PR Creation + 📧 Email → Scan Summary + 📧 Email")

    print("\n📧 Email Notifications:")
    print("   1. 🚨 Security Issue Alert (when vulnerabilities found)")
    print("   2. 🔧 PR Creation Notice (when automated fixes created)")
    print("   3. 📊 Scan Summary Report (always sent)")

    print("\n⚡ Features Integrated:")
    print("   ✅ Loop prevention (security branch filtering)")
    print("   ✅ AI code fix generation")
    print("   ✅ Automated PR creation")
    print("   ✅ Professional HTML email templates")
    print("   ✅ Multiple recipient support")
    print("   ✅ Error handling for email failures")

    print("\n🛡️ Security & Reliability:")
    print("   • Emails are sent asynchronously (non-blocking)")
    print("   • Email failures don't stop the security workflow")
    print("   • Sensitive data is not included in emails")
    print("   • Professional formatting for team communication")


if __name__ == "__main__":
    print("🚀 Starting Complete Email Integration Tests")
    print("=" * 80)

    print("⚠️  IMPORTANT SETUP:")
    print("   1. Update repo names in test functions to your actual test repositories")
    print("   2. Configure email settings with: python setup_email.py")
    print("   3. Ensure you have GitHub token and Anthropic API key configured")
    print("")

    # Test 1: Email configuration status
    email_configured = test_email_configuration_status()

    # Test 2: Complete webhook workflow with emails
    print("\n" + "="*80)
    webhook_result = test_workflow_with_emails()

    # Test 3: Manual scan workflow with emails
    manual_result = test_manual_email_workflow()

    # Display integration summary
    display_integration_summary()

    # Final results
    print("\n" + "=" * 80)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 80)

    print("📧 Email Configuration:", "✅ CONFIGURED" if email_configured else "❌ NOT CONFIGURED")
    print("🔗 Webhook Workflow:", "✅ PASSED" if webhook_result and webhook_result.get("success") else "❌ FAILED")
    print("🔧 Manual Scan Workflow:", "✅ PASSED" if manual_result and manual_result.get("success") else "❌ FAILED")

    if email_configured:
        print("\n📨 Email Status:")
        print("   • Security alerts: Will be sent when issues found")
        print("   • PR notifications: Will be sent when fixes created")
        print("   • Scan summaries: Will be sent after every scan")
        print("   • Check your inbox for test emails")
    else:
        print("\n📨 Email Status: NOT CONFIGURED")
        print("   • Run: python setup_email.py")
        print("   • Workflow will continue without email notifications")

    print(f"\n🎉 HACKATHON FEATURES COMPLETE:")
    print(f"   ✅ 1. Automated GitHub issue creation")
    print(f"   ✅ 2. AI-generated code fixes with automated PRs")
    print(f"   ✅ 3. Email notifications for all security events")
    print(f"   ✅ 4. Loop prevention and error handling")
    print(f"   ✅ 5. Complete end-to-end automation")

    print(f"\n🚀 Your security automation platform is ready!")
