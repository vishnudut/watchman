#!/usr/bin/env python3
"""
Test script for GitHub PR creation functionality
Tests the new create_security_fix_pr method in GitHubHandler
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from github_handler import GitHubHandler
from bedrock_agent import BedrockAgentCore


def test_pr_creation():
    """Test the new PR creation functionality"""
    print("🧪 Testing GitHub PR Creation")
    print("=" * 50)

    try:
        # Initialize GitHub handler
        github_handler = GitHubHandler()

        # Mock code fixes (output from AI)
        test_code_fixes = {
            "summary": "Fix SQL injection and hardcoded secrets vulnerabilities",
            "commit_message": "security: fix SQL injection and secrets exposure",
            "file_changes": [
                {
                    "file_path": "app.py",
                    "issue_type": "sql-injection",
                    "description": "Replace string concatenation with parameterized queries",
                    "changes": [
                        {
                            "line_start": 45,
                            "line_end": 45,
                            "old_code": "query = \"SELECT * FROM users WHERE id = '\" + user_id + \"'\"",
                            "new_code": "query = \"SELECT * FROM users WHERE id = %s\"\ncursor.execute(query, (user_id,))",
                            "explanation": "Use parameterized queries to prevent SQL injection"
                        }
                    ]
                },
                {
                    "file_path": "config.py",
                    "issue_type": "hardcoded-secrets",
                    "description": "Move API keys to environment variables",
                    "changes": [
                        {
                            "line_start": 12,
                            "line_end": 12,
                            "old_code": "API_KEY = 'sk-1234567890abcdef'",
                            "new_code": "import os\n\nAPI_KEY = os.environ.get('APP_API_KEY', '')\nif not API_KEY:\n    raise ValueError('APP_API_KEY environment variable is required')",
                            "explanation": "Load API key from environment variable for security"
                        }
                    ]
                }
            ],
            "additional_files": [
                {
                    "file_path": ".env.example",
                    "content": "# Application Configuration\nAPP_API_KEY=your-secret-api-key-here\n\n# Security Settings\nSECRET_KEY=your-secret-key-here\n",
                    "purpose": "Template for environment variables configuration"
                }
            ]
        }

        # Mock analysis metadata
        test_analysis_metadata = {
            "repo_name": "your-username/test-repo",  # Replace with actual test repo
            "branch": "main",
            "commit_sha": "abc123def456",
            "scan_timestamp": "2024-01-15T10:30:00Z"
        }

        print(f"🎯 Target Repository: {test_analysis_metadata['repo_name']}")
        print(f"📁 Files to modify: {len(test_code_fixes['file_changes'])}")
        print(f"📄 Additional files: {len(test_code_fixes['additional_files'])}")

        # Create the PR
        print("\n🚀 Creating security fix PR...")
        print("-" * 30)

        pr_result = github_handler.create_security_fix_pr(
            repo_name=test_analysis_metadata['repo_name'],
            code_fixes=test_code_fixes,
            analysis_metadata=test_analysis_metadata
        )

        print("\n✅ PR Creation Results:")
        print("=" * 40)

        if pr_result.get('success'):
            print(f"🎉 SUCCESS! PR created successfully")
            print(f"📋 PR Number: #{pr_result.get('pr_number')}")
            print(f"🔗 PR URL: {pr_result.get('pr_url')}")
            print(f"🌿 Branch: {pr_result.get('branch_name')}")
            print(f"📝 Title: {pr_result.get('title')}")
            print(f"📁 Files Changed: {pr_result.get('files_changed', [])}")
            print(f"⏰ Created: {pr_result.get('created_at')}")
        else:
            print(f"❌ FAILED to create PR")
            print(f"Error: {pr_result.get('error')}")
            if pr_result.get('error_code'):
                print(f"Error Code: {pr_result.get('error_code')}")
            if pr_result.get('branch_name'):
                print(f"Branch created: {pr_result.get('branch_name')}")

        # Save results
        results_file = "test_pr_creation_results.json"
        with open(results_file, 'w') as f:
            json.dump(pr_result, f, indent=2)
        print(f"\n💾 Full results saved to: {results_file}")

        return pr_result

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_end_to_end_workflow():
    """Test complete workflow: Analysis → Code Fixes → PR Creation"""
    print("\n" + "=" * 60)
    print("🔗 Testing End-to-End Workflow")
    print("=" * 60)

    try:
        # Initialize components
        ai_agent = BedrockAgentCore()
        github_handler = GitHubHandler()

        # Mock scan results
        mock_scan_results = {
            "total_findings": 2,
            "by_severity": {
                "ERROR": [
                    {
                        "rule_id": "python.lang.security.audit.sql-injection-db",
                        "message": "Possible SQL injection vulnerability",
                        "file": "app.py",
                        "line": 45,
                        "code": "query = \"SELECT * FROM users WHERE id = '\" + user_id + \"'\""
                    }
                ],
                "WARNING": [
                    {
                        "rule_id": "python.lang.security.audit.hardcoded-password",
                        "message": "Hardcoded API key detected",
                        "file": "config.py",
                        "line": 12,
                        "code": "API_KEY = 'sk-1234567890abcdef'"
                    }
                ]
            }
        }

        mock_repo_context = {
            "repo_name": "your-username/test-repo",  # Replace with actual test repo
            "branch": "main",
            "commit_sha": "e2e123test"
        }

        print("🔍 Step 1: Running security analysis...")
        analysis = ai_agent.analyze_security_findings(mock_scan_results, mock_repo_context)

        if not analysis.get('critical_issues'):
            print("⚠️ No critical issues found, skipping fix generation")
            return None

        print(f"✅ Found {len(analysis['critical_issues'])} critical issues")

        print("\n🔧 Step 2: Generating code fixes...")
        code_fixes = ai_agent.generate_code_fixes(analysis['critical_issues'], mock_repo_context)

        if code_fixes.get('error'):
            print(f"❌ Fix generation failed: {code_fixes['error']}")
            return None

        print(f"✅ Generated fixes for {len(code_fixes.get('file_changes', []))} files")

        print("\n🚀 Step 3: Creating GitHub PR...")
        pr_result = github_handler.create_security_fix_pr(
            repo_name=mock_repo_context['repo_name'],
            code_fixes=code_fixes,
            analysis_metadata=mock_repo_context
        )

        print("\n🎯 End-to-End Results:")
        print("=" * 30)

        if pr_result.get('success'):
            print("✅ COMPLETE WORKFLOW SUCCESS!")
            print(f"📋 Analysis: {len(analysis['critical_issues'])} issues")
            print(f"🔧 Fixes: {len(code_fixes.get('file_changes', []))} files")
            print(f"🚀 PR: #{pr_result.get('pr_number')} created")
            print(f"🔗 URL: {pr_result.get('pr_url')}")
        else:
            print("❌ Workflow completed with errors")
            print(f"PR Creation Error: {pr_result.get('error')}")

        # Save complete workflow results
        workflow_results = {
            "analysis": analysis,
            "code_fixes": code_fixes,
            "pr_creation": pr_result
        }

        with open("test_e2e_workflow_results.json", 'w') as f:
            json.dump(workflow_results, f, indent=2)

        print("💾 Complete workflow results saved to: test_e2e_workflow_results.json")
        return workflow_results

    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_code_change_application():
    """Test the code change application logic"""
    print("\n" + "=" * 50)
    print("🔧 Testing Code Change Application")
    print("=" * 50)

    try:
        github_handler = GitHubHandler()

        # Test content
        original_content = """def get_user(user_id):
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    cursor.execute(query)
    return cursor.fetchone()

def another_function():
    return "hello"
"""

        # Mock changes
        test_changes = [
            {
                "line_start": 2,
                "line_end": 3,
                "old_code": "    query = \"SELECT * FROM users WHERE id = '\" + user_id + \"'\"\n    cursor.execute(query)",
                "new_code": "    query = \"SELECT * FROM users WHERE id = %s\"\n    cursor.execute(query, (user_id,))",
                "explanation": "Fix SQL injection vulnerability"
            }
        ]

        print("📝 Original content:")
        print("-" * 20)
        print(original_content)

        print("\n🔧 Applying changes...")
        modified_content = github_handler._apply_code_changes(original_content, test_changes)

        print("\n📝 Modified content:")
        print("-" * 20)
        print(modified_content)

        # Verify the change was applied
        if "cursor.execute(query, (user_id,))" in modified_content:
            print("\n✅ Code change application: SUCCESS")
        else:
            print("\n❌ Code change application: FAILED")

        return modified_content

    except Exception as e:
        print(f"❌ Code change test failed: {e}")
        return None


if __name__ == "__main__":
    print("🚀 Starting GitHub PR Creation Tests")
    print("=" * 70)

    print("⚠️  IMPORTANT: Make sure you have:")
    print("   1. GITHUB_TOKEN set in your .env file")
    print("   2. A test repository you can create PRs in")
    print("   3. Updated the repo_name in the test functions")
    print("")

    # Ask for confirmation
    response = input("Do you want to continue with PR creation tests? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Tests cancelled by user")
        sys.exit(0)

    # Test 1: Code change application (safe, no GitHub API calls)
    print("\n" + "="*50)
    code_change_result = test_code_change_application()

    # Test 2: Basic PR creation
    basic_pr_result = test_pr_creation()

    # Test 3: End-to-end workflow
    e2e_result = test_end_to_end_workflow()

    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)

    if code_change_result and "cursor.execute(query, (user_id,))" in code_change_result:
        print("✅ Code change application: PASSED")
    else:
        print("❌ Code change application: FAILED")

    if basic_pr_result and basic_pr_result.get('success'):
        print("✅ Basic PR creation: PASSED")
    else:
        print("❌ Basic PR creation: FAILED")

    if e2e_result and e2e_result.get('pr_creation', {}).get('success'):
        print("✅ End-to-end workflow: PASSED")
    else:
        print("❌ End-to-end workflow: FAILED")

    print("\n🎯 Next Steps:")
    print("1. Check the created PRs in your test repository")
    print("2. Review the generated code changes")
    print("3. Test with real scan results")
    print("4. Integrate into the main orchestrator workflow")

    if basic_pr_result and basic_pr_result.get('success'):
        print(f"5. Review PR: {basic_pr_result.get('pr_url')}")
