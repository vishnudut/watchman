#!/usr/bin/env python3
"""
Test script for AI code fix generation functionality
Tests the new generate_code_fixes method in BedrockAgentCore
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from bedrock_agent import BedrockAgentCore


def test_code_fix_generation():
    """Test the new code fix generation functionality"""
    print("🧪 Testing AI Code Fix Generation")
    print("=" * 50)

    try:
        # Initialize AI agent
        agent = BedrockAgentCore()

        # Mock security issues (similar to what the scanner would find)
        test_security_issues = [
            {
                "title": "SQL Injection Vulnerability",
                "severity": "CRITICAL",
                "file": "app.py",
                "line": 45,
                "description": "User input is directly concatenated into SQL query without sanitization",
                "business_impact": "Attackers could access or modify database data",
                "recommended_fix": "Use parameterized queries instead of string concatenation",
                "compliance_mapping": ["OWASP", "CWE-89"]
            },
            {
                "title": "Hardcoded API Key",
                "severity": "HIGH",
                "file": "config.py",
                "line": 12,
                "description": "API key is hardcoded in source code",
                "business_impact": "Exposed credentials could lead to unauthorized access",
                "recommended_fix": "Move secrets to environment variables",
                "compliance_mapping": ["OWASP", "CWE-798"]
            },
            {
                "title": "Cross-Site Scripting (XSS)",
                "severity": "HIGH",
                "file": "templates.py",
                "line": 78,
                "description": "User input rendered without escaping in HTML template",
                "business_impact": "Attackers could execute malicious scripts in user browsers",
                "recommended_fix": "Escape user input before rendering in templates",
                "compliance_mapping": ["OWASP", "CWE-79"]
            }
        ]

        # Mock repository context
        test_repo_context = {
            "repo_name": "example/vulnerable-app",
            "branch": "main",
            "commit_sha": "abc123def456"
        }

        print(f"📝 Testing with {len(test_security_issues)} security issues:")
        for i, issue in enumerate(test_security_issues, 1):
            print(f"  {i}. {issue['title']} ({issue['severity']}) - {issue['file']}:{issue['line']}")

        print("\n🤖 Calling AI to generate code fixes...")
        print("-" * 30)

        # Generate code fixes
        code_fixes = agent.generate_code_fixes(test_security_issues, test_repo_context)

        print("\n✅ Code Fix Generation Results:")
        print("=" * 40)

        # Display results
        if "error" in code_fixes:
            print(f"❌ Error: {code_fixes['error']}")
            if "raw_response" in code_fixes:
                print(f"Raw response: {code_fixes['raw_response'][:200]}...")
        else:
            print(f"📋 Summary: {code_fixes.get('summary', 'No summary')}")
            print(f"💬 Commit Message: {code_fixes.get('commit_message', 'No commit message')}")

            file_changes = code_fixes.get('file_changes', [])
            print(f"\n📁 File Changes ({len(file_changes)} files):")

            for i, file_change in enumerate(file_changes, 1):
                print(f"\n  {i}. {file_change.get('file_path', 'unknown')}")
                print(f"     Issue Type: {file_change.get('issue_type', 'unknown')}")
                print(f"     Description: {file_change.get('description', 'No description')}")

                changes = file_change.get('changes', [])
                print(f"     Changes: {len(changes)} code blocks")

                for j, change in enumerate(changes, 1):
                    print(f"       {j}. Lines {change.get('line_start', '?')}-{change.get('line_end', '?')}")
                    print(f"          Old: {change.get('old_code', 'N/A')[:50]}...")
                    print(f"          New: {change.get('new_code', 'N/A')[:50]}...")
                    print(f"          Why: {change.get('explanation', 'No explanation')}")

            additional_files = code_fixes.get('additional_files', [])
            if additional_files:
                print(f"\n📄 Additional Files ({len(additional_files)} files):")
                for i, new_file in enumerate(additional_files, 1):
                    print(f"  {i}. {new_file.get('file_path', 'unknown')}")
                    print(f"     Purpose: {new_file.get('purpose', 'No purpose specified')}")

        # Save results to file for inspection
        results_file = "test_code_fixes_results.json"
        with open(results_file, 'w') as f:
            json.dump(code_fixes, f, indent=2)
        print(f"\n💾 Full results saved to: {results_file}")

        return code_fixes

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_integration_with_analysis():
    """Test integration with existing security analysis"""
    print("\n" + "=" * 50)
    print("🔗 Testing Integration with Security Analysis")
    print("=" * 50)

    try:
        agent = BedrockAgentCore()

        # Mock scan results (what comes from scanner)
        mock_scan_results = {
            "total_findings": 3,
            "by_severity": {
                "ERROR": [
                    {
                        "rule_id": "python.lang.security.audit.sql-injection-db",
                        "message": "Possible SQL injection. Use parameterized queries.",
                        "file": "app.py",
                        "line": 45,
                        "code": "query = \"SELECT * FROM users WHERE id = '\" + user_id + \"'\""
                    }
                ],
                "WARNING": [
                    {
                        "rule_id": "python.lang.security.audit.hardcoded-password",
                        "message": "Hardcoded secret detected",
                        "file": "config.py",
                        "line": 12,
                        "code": "API_KEY = 'sk-1234567890abcdef'"
                    }
                ]
            }
        }

        mock_repo_context = {
            "repo_name": "test/integration-app",
            "branch": "develop",
            "commit_sha": "integration123"
        }

        print("🔍 Running security analysis first...")
        analysis = agent.analyze_security_findings(mock_scan_results, mock_repo_context)

        print(f"✅ Analysis complete. Found {len(analysis.get('critical_issues', []))} critical issues")

        # Now generate fixes for the critical issues
        if analysis.get('critical_issues'):
            print("\n🔧 Generating fixes for critical issues...")
            fixes = agent.generate_code_fixes(analysis['critical_issues'], mock_repo_context)

            print(f"✅ Generated fixes for {len(fixes.get('file_changes', []))} files")

            # Save integration results
            integration_results = {
                "analysis": analysis,
                "fixes": fixes
            }

            with open("test_integration_results.json", 'w') as f:
                json.dump(integration_results, f, indent=2)

            print("💾 Integration results saved to: test_integration_results.json")
            return integration_results
        else:
            print("⚠️ No critical issues found in analysis")
            return None

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("🚀 Starting Code Fix Generation Tests")
    print("=" * 60)

    # Test 1: Basic code fix generation
    basic_results = test_code_fix_generation()

    # Test 2: Integration with existing analysis
    integration_results = test_integration_with_analysis()

    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    if basic_results and not basic_results.get('error'):
        print("✅ Basic code fix generation: PASSED")
    else:
        print("❌ Basic code fix generation: FAILED")

    if integration_results:
        print("✅ Integration with analysis: PASSED")
    else:
        print("❌ Integration with analysis: FAILED")

    print("\n🎯 Next Steps:")
    print("1. Review the generated JSON files")
    print("2. Verify code fixes make sense")
    print("3. Test with real repository data")
    print("4. Proceed to GitHub PR integration")
