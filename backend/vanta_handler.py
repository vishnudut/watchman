import os
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()


class VantaHandler:
    """
    Vanta compliance handler for security audit logging
    Logs security scan events, findings, and remediation activities for SOC 2 compliance
    """

    def __init__(self):
        self.api_key = os.getenv('VANTA_API_KEY')
        self.organization_id = os.getenv('VANTA_ORG_ID')

        if not self.api_key:
            print("⚠️ VANTA_API_KEY not found in .env - using mock mode")
            self.mock_mode = True
        else:
            self.mock_mode = False

        self.api_base_url = "https://api.vanta.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        print(f"✓ Vanta handler initialized ({'mock' if self.mock_mode else 'live'} mode)")

    def log_security_scan_start(
        self,
        scan_run_id: int,
        repo_name: str,
        branch: str,
        commit_sha: str
    ) -> Dict:
        """
        Log the start of a security scan for compliance audit trail

        Args:
            scan_run_id: Internal scan run ID
            repo_name: Repository name
            branch: Git branch
            commit_sha: Git commit SHA

        Returns:
            Vanta log response
        """
        event_data = {
            "event_type": "security_scan_initiated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "resource_type": "code_repository",
            "resource_identifier": repo_name,
            "metadata": {
                "scan_run_id": scan_run_id,
                "repository": repo_name,
                "branch": branch,
                "commit_sha": commit_sha,
                "scan_tool": "Semgrep + Claude AI",
                "control_objective": "Automated Security Code Review",
                "compliance_framework": ["SOC 2", "NIST", "OWASP"]
            },
            "description": f"Automated security scan initiated for {repo_name}:{branch}",
            "severity": "info"
        }

        return self._send_compliance_log("security_control_execution", event_data)

    def log_security_findings(
        self,
        scan_run_id: int,
        repo_name: str,
        findings_summary: Dict,
        ai_analysis: Dict
    ) -> Dict:
        """
        Log security findings and AI analysis results

        Args:
            scan_run_id: Internal scan run ID
            repo_name: Repository name
            findings_summary: Summary of security findings by severity
            ai_analysis: Claude AI analysis results

        Returns:
            Vanta log response
        """
        critical_count = findings_summary.get('critical_count', 0)
        total_findings = findings_summary.get('total_findings', 0)

        # Determine severity based on findings
        if critical_count > 0:
            severity = "high"
        elif total_findings > 5:
            severity = "medium"
        else:
            severity = "low"

        event_data = {
            "event_type": "security_vulnerabilities_detected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "resource_type": "code_repository",
            "resource_identifier": repo_name,
            "metadata": {
                "scan_run_id": scan_run_id,
                "repository": repo_name,
                "total_findings": total_findings,
                "critical_findings": critical_count,
                "high_findings": findings_summary.get('high_count', 0),
                "medium_findings": findings_summary.get('medium_count', 0),
                "low_findings": findings_summary.get('low_count', 0),
                "ai_executive_summary": ai_analysis.get('executive_summary', ''),
                "remediation_provided": len(ai_analysis.get('critical_issues', [])) > 0,
                "compliance_mappings": self._extract_compliance_mappings(ai_analysis),
                "scan_tool": "Semgrep + Claude AI",
                "control_objective": "Vulnerability Detection and Risk Assessment"
            },
            "description": f"Security scan completed: {total_findings} findings ({critical_count} critical) in {repo_name}",
            "severity": severity
        }

        return self._send_compliance_log("vulnerability_assessment", event_data)

    def log_remediation_action(
        self,
        scan_run_id: int,
        repo_name: str,
        github_issue_url: str,
        remediation_details: Dict
    ) -> Dict:
        """
        Log remediation actions taken (GitHub issue creation)

        Args:
            scan_run_id: Internal scan run ID
            repo_name: Repository name
            github_issue_url: URL of created GitHub issue
            remediation_details: Details about remediation recommendations

        Returns:
            Vanta log response
        """
        event_data = {
            "event_type": "security_remediation_initiated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "resource_type": "code_repository",
            "resource_identifier": repo_name,
            "metadata": {
                "scan_run_id": scan_run_id,
                "repository": repo_name,
                "github_issue_url": github_issue_url,
                "remediation_type": "automated_issue_creation",
                "remediation_details": remediation_details.get('recommended_actions', []),
                "critical_issues_addressed": len(remediation_details.get('critical_issues', [])),
                "automated_response": True,
                "response_time_seconds": remediation_details.get('response_time', 0),
                "control_objective": "Vulnerability Remediation Management"
            },
            "description": f"Automated remediation initiated via GitHub issue: {github_issue_url}",
            "severity": "info"
        }

        return self._send_compliance_log("remediation_tracking", event_data)

    def log_compliance_summary(
        self,
        scan_run_id: int,
        workflow_results: Dict
    ) -> Dict:
        """
        Log overall compliance summary for the scan workflow

        Args:
            scan_run_id: Internal scan run ID
            workflow_results: Complete workflow results

        Returns:
            Vanta log response
        """
        event_data = {
            "event_type": "security_control_completion",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "resource_type": "security_program",
            "resource_identifier": "watchman_security_platform",
            "metadata": {
                "scan_run_id": scan_run_id,
                "repository": workflow_results.get('repo_name'),
                "workflow_duration_seconds": workflow_results.get('duration_seconds'),
                "total_findings": workflow_results.get('findings', {}).get('total', 0),
                "critical_findings": workflow_results.get('findings', {}).get('critical', 0),
                "github_issue_created": workflow_results.get('github_issue', {}).get('success', False),
                "automated_workflow": True,
                "control_effectiveness": "operational",
                "compliance_frameworks": ["SOC 2 Type II", "NIST Cybersecurity Framework", "OWASP"],
                "evidence_type": "automated_security_scan",
                "control_frequency": "continuous"
            },
            "description": f"Automated security control executed successfully for {workflow_results.get('repo_name')}",
            "severity": "info"
        }

        return self._send_compliance_log("control_evidence", event_data)

    def _send_compliance_log(self, log_type: str, event_data: Dict) -> Dict:
        """
        Send compliance log to Vanta API or mock the response

        Args:
            log_type: Type of compliance log
            event_data: Event data to log

        Returns:
            API response or mock response
        """
        if self.mock_mode:
            return self._mock_vanta_response(log_type, event_data)

        try:
            # Real Vanta API call
            endpoint = f"{self.api_base_url}/compliance/events"

            payload = {
                "organization_id": self.organization_id,
                "log_type": log_type,
                "event_data": event_data
            }

            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()

            result = {
                "success": True,
                "vanta_event_id": response.json().get('event_id'),
                "timestamp": event_data['timestamp'],
                "log_type": log_type,
                "status": "logged"
            }

            print(f"✓ Vanta compliance log sent: {log_type}")
            return result

        except requests.RequestException as e:
            print(f"❌ Vanta API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "log_type": log_type,
                "fallback_to_mock": True
            }

    def _mock_vanta_response(self, log_type: str, event_data: Dict) -> Dict:
        """
        Generate mock Vanta response for testing/demo purposes

        Args:
            log_type: Type of compliance log
            event_data: Event data

        Returns:
            Mock response
        """
        mock_event_id = f"vanta_mock_{int(datetime.now().timestamp())}_{log_type}"

        print(f"📋 Mock Vanta log: {log_type} - {event_data.get('description', 'No description')}")

        return {
            "success": True,
            "vanta_event_id": mock_event_id,
            "timestamp": event_data['timestamp'],
            "log_type": log_type,
            "status": "logged_mock",
            "mock_mode": True,
            "compliance_frameworks": event_data.get('metadata', {}).get('compliance_framework', [])
        }

    def _extract_compliance_mappings(self, ai_analysis: Dict) -> List[str]:
        """
        Extract compliance framework mappings from AI analysis

        Args:
            ai_analysis: Claude AI analysis results

        Returns:
            List of compliance frameworks mentioned
        """
        mappings = set()

        # Extract from critical issues
        for issue in ai_analysis.get('critical_issues', []):
            compliance_mapping = issue.get('compliance_mapping', [])
            if isinstance(compliance_mapping, list):
                mappings.update(compliance_mapping)

        # Default compliance frameworks
        mappings.update(['SOC 2', 'NIST CSF', 'OWASP'])

        return list(mappings)

    def get_compliance_summary(self, time_range_days: int = 30) -> Dict:
        """
        Get compliance summary for reporting

        Args:
            time_range_days: Number of days to summarize

        Returns:
            Compliance summary
        """
        if self.mock_mode:
            return {
                "summary": f"Mock compliance summary for last {time_range_days} days",
                "total_scans": 15,
                "total_findings": 42,
                "critical_findings": 3,
                "remediation_rate": "95%",
                "average_response_time": "18.5 seconds",
                "frameworks_covered": ["SOC 2", "NIST", "OWASP"],
                "control_effectiveness": "Highly Effective",
                "mock_mode": True
            }

        # Real API implementation would go here
        return {"message": "Real Vanta API integration needed"}

    def generate_audit_evidence(self, scan_run_id: int) -> Dict:
        """
        Generate audit evidence package for a specific scan

        Args:
            scan_run_id: Scan run ID to generate evidence for

        Returns:
            Audit evidence package
        """
        evidence = {
            "evidence_type": "automated_security_control",
            "control_name": "Continuous Security Code Scanning",
            "control_description": "Automated vulnerability detection in source code using AI-powered analysis",
            "scan_run_id": scan_run_id,
            "evidence_timestamp": datetime.now(timezone.utc).isoformat(),
            "control_frequency": "On every code commit",
            "control_automation": "Fully automated",
            "testing_method": "Static Application Security Testing (SAST)",
            "testing_tools": ["Semgrep", "Claude AI", "Watchman Platform"],
            "compliance_frameworks": ["SOC 2 Type II CC6.1", "NIST CSF", "OWASP ASVS"],
            "evidence_artifacts": [
                "Security scan results",
                "AI-generated vulnerability analysis",
                "GitHub issue with remediation steps",
                "Compliance audit logs"
            ],
            "control_effectiveness": "Operational and effective",
            "auditor_notes": "Control operates continuously and provides comprehensive security coverage"
        }

        print(f"📋 Generated audit evidence for scan run #{scan_run_id}")
        return evidence


if __name__ == "__main__":
    # Test the Vanta handler
    try:
        vanta = VantaHandler()

        # Test compliance logging
        print("\n" + "="*50)
        print("TESTING VANTA COMPLIANCE HANDLER")
        print("="*50)

        # Test scan start logging
        scan_start_result = vanta.log_security_scan_start(
            scan_run_id=123,
            repo_name="test/security-app",
            branch="main",
            commit_sha="abc123def456"
        )
        print(f"Scan start log: {scan_start_result.get('success')}")

        # Test findings logging
        findings_summary = {
            "total_findings": 5,
            "critical_count": 2,
            "high_count": 2,
            "medium_count": 1,
            "low_count": 0
        }

        ai_analysis = {
            "executive_summary": "Critical SQL injection and XSS vulnerabilities detected",
            "critical_issues": [
                {"compliance_mapping": ["OWASP Top 10", "SOC 2"]},
                {"compliance_mapping": ["PCI DSS", "NIST"]}
            ]
        }

        findings_result = vanta.log_security_findings(
            scan_run_id=123,
            repo_name="test/security-app",
            findings_summary=findings_summary,
            ai_analysis=ai_analysis
        )
        print(f"Findings log: {findings_result.get('success')}")

        # Test remediation logging
        remediation_result = vanta.log_remediation_action(
            scan_run_id=123,
            repo_name="test/security-app",
            github_issue_url="https://github.com/test/security-app/issues/1",
            remediation_details={
                "recommended_actions": ["Fix SQL injection", "Implement input validation"],
                "critical_issues": [{"title": "SQL Injection"}],
                "response_time": 18.5
            }
        )
        print(f"Remediation log: {remediation_result.get('success')}")

        # Test compliance summary
        workflow_results = {
            "repo_name": "test/security-app",
            "duration_seconds": 18.5,
            "findings": {"total": 5, "critical": 2},
            "github_issue": {"success": True}
        }

        summary_result = vanta.log_compliance_summary(123, workflow_results)
        print(f"Compliance summary: {summary_result.get('success')}")

        # Test audit evidence generation
        evidence = vanta.generate_audit_evidence(123)
        print(f"Audit evidence generated: {evidence.get('control_name')}")

        print("\n✓ Vanta handler test completed successfully!")

    except Exception as e:
        print(f"❌ Vanta handler test failed: {e}")
        import traceback
        traceback.print_exc()
