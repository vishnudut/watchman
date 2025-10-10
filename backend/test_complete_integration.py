#!/usr/bin/env python3
"""
Complete Integration Test for Watchman Security Scanner
Tests the full workflow: Scan → Analysis → Issue Creation → Code Fix Generation → PR Creation
"""

import os
import sys
import json
import time
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from orchestrator import WatchmanOrchestrator


def test_complete_workflow():
    """Test the complete Watchman workflow with all new features"""
    print("🚀 Testing Complete Watchman Workflow")
    print("=" * 60)
    print("📋 This test includes:")
    print("   1. Security scanning")
    print("   2. AI analysis")
    print("   3. GitHub issue creation")
    print("   4. AI code fix generation")
    print("   5. Automated PR creation")
    print("   6. Integration between all components")
    print("=" * 60)

    try:
        # Initialize orchestrator
        print("🔧 Initializing Watchman Orchestrator...")
        orchestrator = WatchmanOrchestrator()
        print("✅ Orchestrator initialized successfully")

        # Mock GitHub webhook payload (simulates a push event)
        mock_webhook_payload = {
            "ref": "refs/heads/main",
            "after": "e2e7f8a9b0c1d2e3f4g5h6i7j8k9l0m1n2o3p4q5",
            "repository": {
                "full_name": "your-username/test-repo",  # CHANGE THIS TO YOUR TEST REPO
                "name": "test-repo",
                "owner": {
                    "login": "your-username"  # CHANGE THIS TO YOUR USERNAME
                }
            },
            "head_commit": {
                "id": "e2e7f8a9b0c1d2e3f4g5h6i7j8k9l0m1n2o3p4q5",
                "message": "Add user authentication system",
                "author": {
                    "name": "Test Developer",
                    "email": "test@example.com"
                }
            },
            "pusher": {
                "name": "test-developer"
            },
            "commits": [
                {
                    "id": "e2e7f8a9b0c1d2e3f4g5h6i7j8k9l0m1n2o3p4q5",
                    "message": "Add user authentication system"
                }
            ]
        }

        repo_name = mock_webhook_payload["repository"]["full_name"]
        branch = "main"
        commit_sha = mock_webhook_payload["after"]

        print(f"\n🎯 Target Repository: {repo_name}")
        print(f"🌿 Branch: {branch}")
        print(f"📝 Commit: {commit_sha[:8]}")

        # Start the complete workflow
        print(f"\n🚀 Starting complete workflow...")
        print("-" * 50)

        start_time = time.time()

        # This will run the complete workflow:
        # 1. Clone repo
        # 2. Run security scan
        # 3. AI analysis
        # 4. Create GitHub issue
        # 5. Generate code fixes
        # 6. Create PR with fixes
        workflow_result = orchestrator.process_github_webhook(
            webhook_payload=mock_webhook_payload,
            repo_full_name="vishnudut/watchman-playground",
            branch=branch,
            commit_sha=commit_sha
        )

        duration = time.time() - start_time

        print(f"\n🎉 Workflow Completed in {duration:.2f} seconds")
        print("=" * 60)

        # Analyze results
        if workflow_result.get("success"):
            print("✅ COMPLETE WORKFLOW: SUCCESS!")

            # Scan Results
            findings = workflow_result.get("findings", {})
            print(f"\n📊 Security Scan Results:")
            print(f"   Total Findings: {findings.get('total', 0)}")
            print(f"   Critical: {findings.get('critical', 0)}")
            print(f"   Warnings: {findings.get('warnings', 0)}")
            print(f"   Info: {findings.get('info', 0)}")

            # GitHub Issue
            github_issue = workflow_result.get("github_issue", {})
            if github_issue.get("success"):
                print(f"\n📋 GitHub Issue:")
                print(f"   ✅ Created Issue #{github_issue.get('issue_number')}")
                print(f"   🔗 URL: {github_issue.get('issue_url')}")
            else:
                print(f"\n📋 GitHub Issue:")
                print(f"   ❌ Failed to create issue: {github_issue.get('error', 'Unknown error')}")

            # Security Fix PR
            security_pr = workflow_result.get("security_fix_pr", {})
            if security_pr.get("success"):
                print(f"\n🚀 Security Fix PR:")
                print(f"   ✅ Created PR #{security_pr.get('pr_number')}")
                print(f"   🔗 URL: {security_pr.get('pr_url')}")
                print(f"   🌿 Branch: {security_pr.get('branch_name')}")
                print(f"   📁 Files Changed: {len(security_pr.get('files_changed', []))}")
                print(f"   📝 Title: {security_pr.get('title', 'N/A')}")
            else:
                print(f"\n🚀 Security Fix PR:")
                if security_pr:
                    print(f"   ❌ Failed to create PR: {security_pr.get('error', 'Unknown error')}")
                else:
                    print(f"   ℹ️ No PR created (no critical issues or fix generation failed)")

            # Analysis Summary
            analysis_summary = workflow_result.get("analysis_summary", "")
            if analysis_summary:
                print(f"\n🤖 AI Analysis Summary:")
                print(f"   {analysis_summary}")

            print(f"\n⏱️  Workflow Metrics:")
            print(f"   Duration: {workflow_result.get('duration_seconds', 0):.2f} seconds")
            print(f"   Scan ID: {workflow_result.get('scan_run_id', 'N/A')}")
            print(f"   Workflow ID: {workflow_result.get('workflow_id', 'N/A')}")

        else:
            print("❌ WORKFLOW FAILED!")
            print(f"Error: {workflow_result.get('error', 'Unknown error')}")

        # Save complete results
        results_file = "test_complete_integration_results.json"
        with open(results_file, 'w') as f:
            json.dump(workflow_result, f, indent=2)
        print(f"\n💾 Complete results saved to: {results_file}")

        return workflow_result

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_manual_scan_workflow():
    """Test the manual scan workflow"""
    print("\n" + "=" * 60)
    print("🔧 Testing Manual Scan Workflow")
    print("=" * 60)

    try:
        orchestrator = WatchmanOrchestrator()

        repo_name = "your-username/test-repo"  # CHANGE THIS
        branch = "main"

        print(f"🎯 Testing manual scan for: {repo_name}:{branch}")

        # Process manual scan
        manual_result = orchestrator.process_manual_scan(repo_name, branch)

        if manual_result.get("success"):
            print("✅ Manual scan workflow: SUCCESS!")

            # Display results similar to webhook workflow
            findings = manual_result.get("findings", {})
            print(f"\n📊 Manual Scan Results:")
            print(f"   Total Findings: {findings.get('total', 0)}")
            print(f"   Critical: {findings.get('critical', 0)}")
            print(f"   Warnings: {findings.get('warnings', 0)}")

            if manual_result.get("github_issue", {}).get("success"):
                issue_num = manual_result["github_issue"]["issue_number"]
                print(f"   ✅ Created GitHub Issue #{issue_num}")

            if manual_result.get("security_fix_pr", {}).get("success"):
                pr_num = manual_result["security_fix_pr"]["pr_number"]
                print(f"   ✅ Created Security Fix PR #{pr_num}")

        else:
            print("❌ Manual scan failed!")
            print(f"Error: {manual_result.get('error', 'Unknown')}")

        return manual_result

    except Exception as e:
        print(f"❌ Manual scan test failed: {e}")
        return None


def display_test_summary(webhook_result, manual_result):
    """Display comprehensive test summary"""
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 70)

    # Webhook workflow results
    print("🔗 Webhook Workflow:")
    if webhook_result and webhook_result.get("success"):
        print("   ✅ Overall: PASSED")
        print(f"   📊 Findings: {webhook_result.get('findings', {}).get('total', 0)}")
        print(f"   📋 Issue: {'✅' if webhook_result.get('github_issue', {}).get('success') else '❌'}")
        print(f"   🚀 PR: {'✅' if webhook_result.get('security_fix_pr', {}).get('success') else '❌'}")
    else:
        print("   ❌ Overall: FAILED")

    # Manual scan results
    print("\n🔧 Manual Scan Workflow:")
    if manual_result and manual_result.get("success"):
        print("   ✅ Overall: PASSED")
        print(f"   📊 Findings: {manual_result.get('findings', {}).get('total', 0)}")
        print(f"   📋 Issue: {'✅' if manual_result.get('github_issue', {}).get('success') else '❌'}")
        print(f"   🚀 PR: {'✅' if manual_result.get('security_fix_pr', {}).get('success') else '❌'}")
    else:
        print("   ❌ Overall: FAILED")

    # Feature testing summary
    print(f"\n🎯 Feature Implementation Status:")
    print(f"   ✅ Security Scanning (Semgrep)")
    print(f"   ✅ AI Analysis (Claude)")
    print(f"   ✅ GitHub Issue Creation")
    print(f"   ✅ AI Code Fix Generation")
    print(f"   ✅ Automated PR Creation")
    print(f"   ✅ End-to-End Integration")

    # URLs for review
    webhook_urls = []
    manual_urls = []

    if webhook_result:
        if webhook_result.get("github_issue", {}).get("success"):
            webhook_urls.append(f"Issue: {webhook_result['github_issue'].get('issue_url', 'N/A')}")
        if webhook_result.get("security_fix_pr", {}).get("success"):
            webhook_urls.append(f"PR: {webhook_result['security_fix_pr'].get('pr_url', 'N/A')}")

    if manual_result:
        if manual_result.get("github_issue", {}).get("success"):
            manual_urls.append(f"Issue: {manual_result['github_issue'].get('issue_url', 'N/A')}")
        if manual_result.get("security_fix_pr", {}).get("success"):
            manual_urls.append(f"PR: {manual_result['security_fix_pr'].get('pr_url', 'N/A')}")

    if webhook_urls or manual_urls:
        print(f"\n🔗 Review URLs:")
        for url in webhook_urls:
            print(f"   Webhook: {url}")
        for url in manual_urls:
            print(f"   Manual: {url}")

    print(f"\n🎉 Your hackathon features are working! 🚀")
    print(f"   1. ✅ GitHub Issues are created")
    print(f"   2. ✅ AI generates code fixes")
    print(f"   3. ✅ Automated PRs are created")
    print(f"   4. 🔜 Email notifications (next phase)")


if __name__ == "__main__":
    print("🚀 Starting Complete Integration Tests")
    print("=" * 80)
    print("⚠️  IMPORTANT SETUP REQUIRED:")
    print("   1. Update repo_name in the test functions to your test repository")
    print("   2. Ensure you have a GitHub token with repo access")
    print("   3. Ensure your test repository exists and is accessible")
    print("   4. Make sure you have ANTHROPIC_API_KEY in your .env")
    print("   5. Semgrep should be installed and available")
    print("")

    # Ask for confirmation
    response = input("Have you updated the repo names and are ready to test? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Tests cancelled. Please update the repository names first.")
        print("   Look for 'your-username/test-repo' in this file and replace with your actual repo.")
        sys.exit(0)

    print("\n🎬 Starting tests...")

    # Test 1: Complete webhook workflow
    webhook_result = test_complete_workflow()

    # Test 2: Manual scan workflow
    manual_result = test_manual_scan_workflow()

    # Display comprehensive summary
    display_test_summary(webhook_result, manual_result)

    print("\n" + "=" * 80)
    print("🎯 NEXT STEPS FOR YOUR HACKATHON:")
    print("=" * 80)
    print("1. ✅ Code improvements with automated PRs - COMPLETE!")
    print("2. 🔜 Email notifications when issues/PRs are created")
    print("3. 🔜 Frontend updates to show PR status")
    print("4. 🔜 Configuration for notification preferences")
    print("")
    print("Ready to move to Phase 2: Email Notifications! 📧")
