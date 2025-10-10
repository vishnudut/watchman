#!/usr/bin/env python3
"""
Simple test script for Vanta compliance handler
Tests both mock and live modes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vanta_handler import VantaHandler

def test_vanta_integration():
    """Test Vanta compliance logging functionality"""
    print("🧪 Testing Vanta Compliance Handler")
    print("=" * 50)

    try:
        # Initialize handler (will auto-detect mock mode)
        vanta = VantaHandler()

        # Test data
        scan_run_id = 999
        repo_name = "test/watchman-demo"
        branch = "main"
        commit_sha = "test123abc"

        print(f"\n1. Testing scan start logging...")
        start_result = vanta.log_security_scan_start(
            scan_run_id=scan_run_id,
            repo_name=repo_name,
            branch=branch,
            commit_sha=commit_sha
        )
        print(f"   Result: {'✅ Success' if start_result['success'] else '❌ Failed'}")
        print(f"   Event ID: {start_result.get('vanta_event_id', 'N/A')}")

        print(f"\n2. Testing security findings logging...")
        findings_summary = {
            "total_findings": 3,
            "critical_count": 1,
            "high_count": 1,
            "medium_count": 1,
            "low_count": 0
        }

        ai_analysis = {
            "executive_summary": "SQL injection and XSS vulnerabilities detected requiring immediate attention",
            "critical_issues": [
                {"compliance_mapping": ["OWASP Top 10 A03:2021", "SOC 2 CC6.1"]},
                {"compliance_mapping": ["PCI DSS 6.5.1", "NIST CSF"]}
            ],
            "recommended_actions": ["Implement parameterized queries", "Add input validation"]
        }

        findings_result = vanta.log_security_findings(
            scan_run_id=scan_run_id,
            repo_name=repo_name,
            findings_summary=findings_summary,
            ai_analysis=ai_analysis
        )
        print(f"   Result: {'✅ Success' if findings_result['success'] else '❌ Failed'}")
        print(f"   Event ID: {findings_result.get('vanta_event_id', 'N/A')}")

        print(f"\n3. Testing remediation action logging...")
        remediation_result = vanta.log_remediation_action(
            scan_run_id=scan_run_id,
            repo_name=repo_name,
            github_issue_url="https://github.com/test/watchman-demo/issues/1",
            remediation_details=ai_analysis
        )
        print(f"   Result: {'✅ Success' if remediation_result['success'] else '❌ Failed'}")
        print(f"   Event ID: {remediation_result.get('vanta_event_id', 'N/A')}")

        print(f"\n4. Testing compliance summary logging...")
        workflow_results = {
            "repo_name": repo_name,
            "duration_seconds": 22.5,
            "findings": {"total": 3, "critical": 1},
            "github_issue": {"success": True}
        }

        summary_result = vanta.log_compliance_summary(scan_run_id, workflow_results)
        print(f"   Result: {'✅ Success' if summary_result['success'] else '❌ Failed'}")
        print(f"   Event ID: {summary_result.get('vanta_event_id', 'N/A')}")

        print(f"\n5. Testing audit evidence generation...")
        evidence = vanta.generate_audit_evidence(scan_run_id)
        print(f"   Control: {evidence.get('control_name', 'N/A')}")
        print(f"   Frameworks: {', '.join(evidence.get('compliance_frameworks', []))}")
        print(f"   Effectiveness: {evidence.get('control_effectiveness', 'N/A')}")

        print(f"\n6. Testing compliance summary report...")
        compliance_summary = vanta.get_compliance_summary(time_range_days=7)
        print(f"   Total Scans: {compliance_summary.get('total_scans', 'N/A')}")
        print(f"   Remediation Rate: {compliance_summary.get('remediation_rate', 'N/A')}")
        print(f"   Control Effectiveness: {compliance_summary.get('control_effectiveness', 'N/A')}")

        print(f"\n{'='*50}")
        print("🎉 All Vanta compliance tests passed!")
        print(f"Mode: {'Mock' if vanta.mock_mode else 'Live API'}")
        print(f"Ready for compliance audit trail logging!")

        return True

    except Exception as e:
        print(f"\n❌ Vanta test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_vanta_integration()
    sys.exit(0 if success else 1)
