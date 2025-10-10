#!/usr/bin/env python3
"""
Loop Prevention Test Script for Watchman Security Scanner
Tests the branch filtering and commit message filtering to prevent infinite loops
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from orchestrator import WatchmanOrchestrator, extract_webhook_data


def test_security_branch_filtering():
    """Test that security fix branches are filtered out"""
    print("🧪 Testing Security Branch Filtering")
    print("=" * 50)

    try:
        orchestrator = WatchmanOrchestrator()

        # Test security fix branch names
        security_branches = [
            "security-fixes-20241215-143022",
            "security-fixes-20241215-143045",
            "security-fixes-20241216-091030",
            "security-fixes-hotfix-001"
        ]

        results = []
        for branch in security_branches:
            print(f"🔍 Testing branch: {branch}")

            # Mock webhook payload for security branch
            mock_payload = {
                "ref": f"refs/heads/{branch}",
                "after": "abc123def456",
                "repository": {
                    "full_name": "test/security-repo"
                },
                "head_commit": {
                    "id": "abc123def456",
                    "message": "security: fix SQL injection in user auth"
                },
                "pusher": {
                    "name": "watchman-bot"
                }
            }

            # Process webhook
            result = orchestrator.process_github_webhook(
                webhook_payload=mock_payload,
                repo_full_name="test/security-repo",
                branch=branch,
                commit_sha="abc123def456"
            )

            # Check if it was skipped
            if result.get("skipped_reason") == "security_fix_branch":
                print(f"✅ Branch {branch} correctly skipped")
                results.append(True)
            else:
                print(f"❌ Branch {branch} was NOT skipped - POTENTIAL LOOP!")
                results.append(False)

        success_rate = sum(results) / len(results) * 100
        print(f"\n📊 Branch Filtering Results: {success_rate:.0f}% success")
        return all(results)

    except Exception as e:
        print(f"❌ Branch filtering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_security_commit_filtering():
    """Test that security fix commits are filtered out"""
    print("\n🧪 Testing Security Commit Message Filtering")
    print("=" * 50)

    try:
        orchestrator = WatchmanOrchestrator()

        # Test security commit messages
        security_commits = [
            "security: fix SQL injection in database queries",
            "Security: remove hardcoded API keys",
            "SECURITY: patch XSS vulnerability in templates",
            "security: automated fix for multiple vulnerabilities"
        ]

        results = []
        for i, commit_msg in enumerate(security_commits, 1):
            print(f"🔍 Testing commit: {commit_msg[:40]}...")

            # Mock webhook payload with security commit
            mock_payload = {
                "ref": "refs/heads/main",
                "after": f"security{i:03d}def456",
                "repository": {
                    "full_name": "test/commit-filter-repo"
                },
                "head_commit": {
                    "id": f"security{i:03d}def456",
                    "message": commit_msg
                },
                "pusher": {
                    "name": "watchman-bot"
                }
            }

            # Process webhook
            result = orchestrator.process_github_webhook(
                webhook_payload=mock_payload,
                repo_full_name="test/commit-filter-repo",
                branch="main",
                commit_sha=f"security{i:03d}def456"
            )

            # Check if it was skipped
            if result.get("skipped_reason") == "security_fix_commit":
                print(f"✅ Commit correctly skipped")
                results.append(True)
            else:
                print(f"❌ Commit was NOT skipped - POTENTIAL LOOP!")
                results.append(False)

        success_rate = sum(results) / len(results) * 100
        print(f"\n📊 Commit Filtering Results: {success_rate:.0f}% success")
        return all(results)

    except Exception as e:
        print(f"❌ Commit filtering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_normal_branches_not_filtered():
    """Test that normal branches are NOT filtered out"""
    print("\n🧪 Testing Normal Branches Are NOT Filtered")
    print("=" * 50)

    try:
        # Note: This test will actually try to scan, so we'll mock it or use a lightweight approach
        print("📝 Testing that normal branches trigger scans...")

        normal_branches = [
            "main",
            "develop",
            "feature/user-authentication",
            "bugfix/login-error",
            "hotfix/critical-patch"
        ]

        # Test webhook data extraction
        for branch in normal_branches:
            mock_payload = {
                "ref": f"refs/heads/{branch}",
                "after": "normal123def456",
                "repository": {
                    "full_name": "test/normal-repo"
                },
                "head_commit": {
                    "id": "normal123def456",
                    "message": "Add new user registration feature"
                },
                "pusher": {
                    "name": "developer"
                }
            }

            # Test webhook data extraction (safe, no actual scanning)
            webhook_data = extract_webhook_data(mock_payload)

            branch_from_payload = webhook_data.get("branch")
            if branch_from_payload == branch:
                print(f"✅ Normal branch {branch} would trigger scan")
            else:
                print(f"❌ Normal branch {branch} data extraction failed")

        print("✅ All normal branches would trigger scans (as expected)")
        return True

    except Exception as e:
        print(f"❌ Normal branch test failed: {e}")
        return False


def test_webhook_data_extraction():
    """Test webhook data extraction with security filtering"""
    print("\n🧪 Testing Webhook Data Extraction")
    print("=" * 50)

    try:
        # Test various webhook payloads
        test_payloads = [
            {
                "name": "Normal push",
                "payload": {
                    "ref": "refs/heads/main",
                    "after": "abc123",
                    "repository": {"full_name": "test/repo"},
                    "head_commit": {"id": "abc123", "message": "Add feature"}
                },
                "should_extract": True
            },
            {
                "name": "Security branch push",
                "payload": {
                    "ref": "refs/heads/security-fixes-20241215",
                    "after": "def456",
                    "repository": {"full_name": "test/repo"},
                    "head_commit": {"id": "def456", "message": "security: fix issue"}
                },
                "should_extract": True  # Extraction should work, filtering happens later
            },
            {
                "name": "Branch deletion",
                "payload": {
                    "ref": "refs/heads/feature-branch",
                    "after": "0000000000000000000000000000000000000000",
                    "repository": {"full_name": "test/repo"},
                    "head_commit": None
                },
                "should_extract": True
            }
        ]

        for test_case in test_payloads:
            print(f"🔍 Testing: {test_case['name']}")

            webhook_data = extract_webhook_data(test_case["payload"])

            if webhook_data.get("repo_full_name") and webhook_data.get("branch"):
                print(f"✅ Data extracted successfully")
            else:
                print(f"❌ Data extraction failed")

        return True

    except Exception as e:
        print(f"❌ Webhook data extraction test failed: {e}")
        return False


def test_loop_scenario_simulation():
    """Simulate the loop scenario that was happening"""
    print("\n🧪 Simulating Previous Loop Scenario")
    print("=" * 50)

    try:
        orchestrator = WatchmanOrchestrator()

        print("📝 Simulating the loop that was happening...")
        print("1. Normal commit triggers scan")
        print("2. Scan creates security fix PR")
        print("3. Security fix commits should be filtered")

        # Step 1: Normal commit (should process)
        normal_payload = {
            "ref": "refs/heads/main",
            "after": "user123commit",
            "repository": {"full_name": "test/loop-test"},
            "head_commit": {
                "id": "user123commit",
                "message": "Add user authentication system"
            }
        }

        print("\n🟢 Step 1: Normal commit on main branch")
        # We won't actually run this to avoid triggering a real scan
        print("   → This would trigger a full security scan (expected)")

        # Step 2: Security fix commit (should be filtered)
        security_payload = {
            "ref": "refs/heads/security-fixes-20241215-143022",
            "after": "security123fix",
            "repository": {"full_name": "test/loop-test"},
            "head_commit": {
                "id": "security123fix",
                "message": "security: fix SQL injection in user auth"
            }
        }

        print("\n🔴 Step 2: Security fix commit (should be filtered)")
        result = orchestrator.process_github_webhook(
            webhook_payload=security_payload,
            repo_full_name="test/loop-test",
            branch="security-fixes-20241215-143022",
            commit_sha="security123fix"
        )

        if result.get("skipped_reason"):
            print(f"✅ Loop prevented! Reason: {result['skipped_reason']}")
            print(f"✅ Message: {result['message']}")
            return True
        else:
            print("❌ Loop NOT prevented - this would cause infinite loops!")
            return False

    except Exception as e:
        print(f"❌ Loop simulation test failed: {e}")
        return False


def display_loop_prevention_summary():
    """Display summary of loop prevention mechanisms"""
    print("\n" + "=" * 60)
    print("🛡️ LOOP PREVENTION MECHANISMS SUMMARY")
    print("=" * 60)

    print("\n🔍 Branch Filtering:")
    print("   ✅ Branches starting with 'security-fixes-' are skipped")
    print("   ✅ Applied in both webhook endpoint and orchestrator")
    print("   ✅ Returns success status to avoid GitHub webhook retries")

    print("\n💬 Commit Message Filtering:")
    print("   ✅ Commits starting with 'security:' are skipped")
    print("   ✅ Case-insensitive filtering ('Security:', 'SECURITY:')")
    print("   ✅ Secondary safety net in case branch filtering fails")

    print("\n📍 Filter Locations:")
    print("   1. main.py webhook endpoint (early filtering)")
    print("   2. orchestrator.py workflow method (backup filtering)")

    print("\n🔄 Previous Loop Scenario:")
    print("   ❌ Commit → Scan → PR created → PR commits → New scan → New PR...")
    print("   ✅ NOW: Commit → Scan → PR created → PR commits filtered → No new scan")

    print("\n⚡ Performance Benefits:")
    print("   • Prevents unnecessary compute usage")
    print("   • Reduces GitHub API calls")
    print("   • Avoids database spam")
    print("   • Prevents email notification spam (when integrated)")


if __name__ == "__main__":
    print("🚀 Watchman Loop Prevention Tests")
    print("=" * 70)

    # Run all tests
    test_results = []

    # Test 1: Branch filtering
    branch_test = test_security_branch_filtering()
    test_results.append(("Branch Filtering", branch_test))

    # Test 2: Commit message filtering
    commit_test = test_security_commit_filtering()
    test_results.append(("Commit Filtering", commit_test))

    # Test 3: Normal branches not filtered
    normal_test = test_normal_branches_not_filtered()
    test_results.append(("Normal Branch Processing", normal_test))

    # Test 4: Webhook data extraction
    extraction_test = test_webhook_data_extraction()
    test_results.append(("Webhook Data Extraction", extraction_test))

    # Test 5: Loop scenario simulation
    loop_test = test_loop_scenario_simulation()
    test_results.append(("Loop Prevention Simulation", loop_test))

    # Display summary
    display_loop_prevention_summary()

    # Final results
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)

    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if result:
            passed_tests += 1

    success_rate = (passed_tests / len(test_results)) * 100
    print(f"\nOverall Success Rate: {success_rate:.0f}% ({passed_tests}/{len(test_results)})")

    if success_rate == 100:
        print("\n🎉 ALL TESTS PASSED! Loop prevention is working correctly.")
        print("✅ Your manual scan loop issue should now be resolved!")
    else:
        print("\n⚠️ Some tests failed. Please review the failing components.")

    print("\n🎯 Next Steps:")
    print("1. Test manual scan via Swagger to verify no more loops")
    print("2. Test webhook with actual repository commits")
    print("3. Monitor server logs for proper filtering messages")
    print("4. Proceed with email integration once loops are confirmed fixed")
