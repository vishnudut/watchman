import subprocess
import json
from typing import Dict, List
from pathlib import Path


class SecurityScanner:
    """Scans code repositories for security vulnerabilities using Semgrep"""

    def __init__(self):
        self.rules = [
            "p/security-audit",
            "p/owasp-top-ten",
            "p/cwe-top-25"
        ]

    def scan_repository(self, repo_path: str) -> Dict:
        """
        Run Semgrep security scan on a local repository

        Args:
            repo_path: Path to the cloned git repository

        Returns:
            Dictionary with scan results and metadata
        """
        print(f"🔍 Starting security scan on: {repo_path}")

        try:
            # Use specific rule sets instead of auto config to avoid metrics requirement
            cmd = [
                "semgrep",
                "--config", "p/security-audit",
                "--config", "p/owasp-top-ten",
                "--config", "p/cwe-top-25",
                "--json",
                "--metrics", "off",
                "--timeout", "300",
                repo_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode not in [0, 1]:
                return {
                    "error": f"Semgrep failed: {result.stderr}",
                    "total_findings": 0
                }

            raw_findings = json.loads(result.stdout)
            processed = self._process_findings(raw_findings)

            print(f"✓ Scan complete: {processed['total_findings']} findings")
            return processed

        except subprocess.TimeoutExpired:
            print("❌ Scan timeout")
            return {"error": "Scan timeout", "total_findings": 0}

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Semgrep output: {e}")
            return {"error": "Invalid JSON from Semgrep", "total_findings": 0}

        except Exception as e:
            print(f"❌ Scan error: {e}")
            return {"error": str(e), "total_findings": 0}

    def _process_findings(self, raw_findings: Dict) -> Dict:
        """Process raw Semgrep output into structured format"""
        results = {
            "total_findings": 0,
            "by_severity": {
                "ERROR": [],
                "WARNING": [],
                "INFO": []
            },
            "summary": ""
        }

        findings_list = raw_findings.get("results", [])
        results["total_findings"] = len(findings_list)

        for finding in findings_list:
            extra = finding.get("extra", {})
            severity = extra.get("severity", "INFO").upper()

            if severity not in results["by_severity"]:
                severity = "INFO"

            vuln = {
                "rule_id": finding.get("check_id", "unknown"),
                "message": extra.get("message", "No description"),
                "file": finding.get("path", "unknown"),
                "line": finding.get("start", {}).get("line", 0),
                "code_snippet": extra.get("lines", ""),
                "severity": severity,
                "cwe": extra.get("metadata", {}).get("cwe", []),
                "owasp": extra.get("metadata", {}).get("owasp", [])
            }

            results["by_severity"][severity].append(vuln)

        error_count = len(results["by_severity"]["ERROR"])
        warning_count = len(results["by_severity"]["WARNING"])
        info_count = len(results["by_severity"]["INFO"])

        results["summary"] = f"Found {error_count} critical, {warning_count} warnings, {info_count} info"

        return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python scanner.py <path_to_repo>")
        sys.exit(1)

    scanner = SecurityScanner()
    results = scanner.scan_repository(sys.argv[1])

    print("\n" + "="*50)
    print("SCAN RESULTS")
    print("="*50)
    print(json.dumps(results, indent=2))
