import os
import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class DatabaseHandler:
    """
    SQLite database handler for Watchman security scanner
    Stores scan results, analysis data, and system metadata
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', 'watchman.db')

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"✓ Database initialized: {self.db_path}")
        self._initialize_database()

    def _initialize_database(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS scan_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_name TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    commit_sha TEXT NOT NULL,
                    scan_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    scan_status TEXT NOT NULL DEFAULT 'pending',
                    total_findings INTEGER DEFAULT 0,
                    critical_count INTEGER DEFAULT 0,
                    high_count INTEGER DEFAULT 0,
                    medium_count INTEGER DEFAULT 0,
                    low_count INTEGER DEFAULT 0,
                    scan_duration_seconds REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS security_findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_run_id INTEGER NOT NULL,
                    rule_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER,
                    message TEXT NOT NULL,
                    code_snippet TEXT,
                    cwe_ids TEXT,
                    owasp_categories TEXT,
                    status TEXT DEFAULT 'open',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (scan_run_id) REFERENCES scan_runs (id)
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS ai_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_run_id INTEGER NOT NULL,
                    executive_summary TEXT,
                    critical_issues TEXT,
                    recommended_actions TEXT,
                    tools_to_use TEXT,
                    raw_response TEXT,
                    analysis_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (scan_run_id) REFERENCES scan_runs (id)
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS github_issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_run_id INTEGER NOT NULL,
                    issue_number INTEGER NOT NULL,
                    issue_url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    closed_at DATETIME,
                    FOREIGN KEY (scan_run_id) REFERENCES scan_runs (id)
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS vanta_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_run_id INTEGER NOT NULL,
                    log_type TEXT NOT NULL,
                    log_data TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (scan_run_id) REFERENCES scan_runs (id)
                )
            ''')

            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_scan_runs_repo ON scan_runs(repo_name)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_scan_runs_timestamp ON scan_runs(scan_timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_findings_scan_run ON security_findings(scan_run_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_findings_severity ON security_findings(severity)')

            conn.commit()
            print("✓ Database tables initialized")

    def create_scan_run(
        self,
        repo_name: str,
        branch: str,
        commit_sha: str
    ) -> int:
        """
        Create a new scan run record

        Args:
            repo_name: Repository name
            branch: Git branch name
            commit_sha: Git commit SHA

        Returns:
            Scan run ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scan_runs (repo_name, branch, commit_sha, scan_status)
                VALUES (?, ?, ?, 'running')
            ''', (repo_name, branch, commit_sha))

            scan_run_id = cursor.lastrowid
            conn.commit()

            print(f"✓ Created scan run #{scan_run_id} for {repo_name}")
            return scan_run_id

    def update_scan_run(
        self,
        scan_run_id: int,
        status: str,
        total_findings: int = 0,
        finding_counts: Dict[str, int] = None,
        duration: float = None
    ):
        """
        Update scan run with results

        Args:
            scan_run_id: Scan run ID
            status: Scan status (completed, failed, etc.)
            total_findings: Total number of findings
            finding_counts: Dict with counts by severity
            duration: Scan duration in seconds
        """
        if finding_counts is None:
            finding_counts = {}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE scan_runs
                SET scan_status = ?,
                    total_findings = ?,
                    critical_count = ?,
                    high_count = ?,
                    medium_count = ?,
                    low_count = ?,
                    scan_duration_seconds = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                status,
                total_findings,
                finding_counts.get('ERROR', 0),
                finding_counts.get('WARNING', 0),
                finding_counts.get('MEDIUM', 0),
                finding_counts.get('LOW', 0),
                duration,
                scan_run_id
            ))

            conn.commit()
            print(f"✓ Updated scan run #{scan_run_id} - Status: {status}")

    def store_security_findings(
        self,
        scan_run_id: int,
        findings: List[Dict]
    ):
        """
        Store security findings from Semgrep scan

        Args:
            scan_run_id: Scan run ID
            findings: List of finding dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for finding in findings:
                cursor.execute('''
                    INSERT INTO security_findings (
                        scan_run_id, rule_id, severity, file_path, line_number,
                        message, code_snippet, cwe_ids, owasp_categories
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    scan_run_id,
                    finding.get('rule_id', 'unknown'),
                    finding.get('severity', 'INFO'),
                    finding.get('file', 'unknown'),
                    finding.get('line', 0),
                    finding.get('message', ''),
                    finding.get('code_snippet', ''),
                    json.dumps(finding.get('cwe', [])),
                    json.dumps(finding.get('owasp', []))
                ))

            conn.commit()
            print(f"✓ Stored {len(findings)} security findings")

    def store_ai_analysis(
        self,
        scan_run_id: int,
        analysis_results: Dict
    ):
        """
        Store AI analysis results

        Args:
            scan_run_id: Scan run ID
            analysis_results: Analysis results from Claude/OpenAI
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ai_analysis (
                    scan_run_id, executive_summary, critical_issues,
                    recommended_actions, tools_to_use, raw_response
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                scan_run_id,
                analysis_results.get('executive_summary', ''),
                json.dumps(analysis_results.get('critical_issues', [])),
                json.dumps(analysis_results.get('recommended_actions', [])),
                json.dumps(analysis_results.get('tools_to_use', [])),
                analysis_results.get('raw_response', '')
            ))

            conn.commit()
            print(f"✓ Stored AI analysis for scan run #{scan_run_id}")

    def store_github_issue(
        self,
        scan_run_id: int,
        issue_data: Dict
    ):
        """
        Store GitHub issue information

        Args:
            scan_run_id: Scan run ID
            issue_data: GitHub issue creation response
        """
        if not issue_data.get('success'):
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO github_issues (
                    scan_run_id, issue_number, issue_url, title
                ) VALUES (?, ?, ?, ?)
            ''', (
                scan_run_id,
                issue_data.get('issue_number'),
                issue_data.get('issue_url'),
                issue_data.get('title')
            ))

            conn.commit()
            print(f"✓ Stored GitHub issue #{issue_data.get('issue_number')}")

    def store_vanta_log(
        self,
        scan_run_id: int,
        log_type: str,
        log_data: Dict
    ):
        """
        Store Vanta compliance log

        Args:
            scan_run_id: Scan run ID
            log_type: Type of log (audit, compliance, etc.)
            log_data: Log data dictionary
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO vanta_logs (scan_run_id, log_type, log_data)
                VALUES (?, ?, ?)
            ''', (scan_run_id, log_type, json.dumps(log_data)))

            conn.commit()
            print(f"✓ Stored Vanta log: {log_type}")

    def get_scan_run(self, scan_run_id: int) -> Optional[Dict]:
        """Get scan run details by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM scan_runs WHERE id = ?', (scan_run_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def get_recent_scans(self, repo_name: str = None, limit: int = 10) -> List[Dict]:
        """Get recent scan runs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if repo_name:
                cursor.execute('''
                    SELECT * FROM scan_runs
                    WHERE repo_name = ?
                    ORDER BY scan_timestamp DESC
                    LIMIT ?
                ''', (repo_name, limit))
            else:
                cursor.execute('''
                    SELECT * FROM scan_runs
                    ORDER BY scan_timestamp DESC
                    LIMIT ?
                ''', (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_scan_findings(self, scan_run_id: int) -> List[Dict]:
        """Get all findings for a scan run"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM security_findings
                WHERE scan_run_id = ?
                ORDER BY severity, file_path, line_number
            ''', (scan_run_id,))

            findings = []
            for row in cursor.fetchall():
                finding = dict(row)
                # Parse JSON fields
                finding['cwe_ids'] = json.loads(finding['cwe_ids'] or '[]')
                finding['owasp_categories'] = json.loads(finding['owasp_categories'] or '[]')
                findings.append(finding)

            return findings

    def get_ai_analysis(self, scan_run_id: int) -> Optional[Dict]:
        """Get AI analysis for a scan run"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM ai_analysis WHERE scan_run_id = ?', (scan_run_id,))
            row = cursor.fetchone()

            if row:
                analysis = dict(row)
                # Parse JSON fields
                analysis['critical_issues'] = json.loads(analysis['critical_issues'] or '[]')
                analysis['recommended_actions'] = json.loads(analysis['recommended_actions'] or '[]')
                analysis['tools_to_use'] = json.loads(analysis['tools_to_use'] or '[]')
                return analysis

            return None

    def get_scan_summary(self) -> Dict:
        """Get overall scan statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total scans
            cursor.execute('SELECT COUNT(*) FROM scan_runs')
            total_scans = cursor.fetchone()[0]

            # Scans by status
            cursor.execute('SELECT scan_status, COUNT(*) FROM scan_runs GROUP BY scan_status')
            status_counts = dict(cursor.fetchall())

            # Recent activity (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM scan_runs
                WHERE scan_timestamp >= datetime('now', '-7 days')
            ''')
            recent_scans = cursor.fetchone()[0]

            # Total findings
            cursor.execute('SELECT COUNT(*) FROM security_findings')
            total_findings = cursor.fetchone()[0]

            # Findings by severity
            cursor.execute('SELECT severity, COUNT(*) FROM security_findings GROUP BY severity')
            severity_counts = dict(cursor.fetchall())

            return {
                'total_scans': total_scans,
                'status_counts': status_counts,
                'recent_scans_7d': recent_scans,
                'total_findings': total_findings,
                'severity_counts': severity_counts
            }

    def cleanup_old_scans(self, days_old: int = 30):
        """Clean up scan runs older than specified days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get old scan run IDs
            cursor.execute('''
                SELECT id FROM scan_runs
                WHERE scan_timestamp < datetime('now', '-{} days')
            '''.format(days_old))

            old_scan_ids = [row[0] for row in cursor.fetchall()]

            if old_scan_ids:
                # Delete related records
                placeholders = ','.join(['?' for _ in old_scan_ids])

                cursor.execute(f'DELETE FROM security_findings WHERE scan_run_id IN ({placeholders})', old_scan_ids)
                cursor.execute(f'DELETE FROM ai_analysis WHERE scan_run_id IN ({placeholders})', old_scan_ids)
                cursor.execute(f'DELETE FROM github_issues WHERE scan_run_id IN ({placeholders})', old_scan_ids)
                cursor.execute(f'DELETE FROM vanta_logs WHERE scan_run_id IN ({placeholders})', old_scan_ids)
                cursor.execute(f'DELETE FROM scan_runs WHERE id IN ({placeholders})', old_scan_ids)

                conn.commit()
                print(f"✓ Cleaned up {len(old_scan_ids)} old scan runs")
            else:
                print("✓ No old scan runs to clean up")


if __name__ == "__main__":
    # Test the database handler
    try:
        db = DatabaseHandler("test_watchman.db")

        # Test creating a scan run
        scan_id = db.create_scan_run("test/repo", "main", "abc123")

        # Test storing findings
        test_findings = [
            {
                "rule_id": "sql-injection",
                "severity": "ERROR",
                "file": "app.py",
                "line": 45,
                "message": "SQL injection vulnerability",
                "code_snippet": "SELECT * FROM users WHERE id = " + user_id,
                "cwe": ["CWE-89"],
                "owasp": ["A03:2021"]
            }
        ]

        db.store_security_findings(scan_id, test_findings)

        # Test storing AI analysis
        test_analysis = {
            "executive_summary": "Critical SQL injection found",
            "critical_issues": [{"title": "SQL Injection", "severity": "CRITICAL"}],
            "recommended_actions": ["Use parameterized queries"],
            "tools_to_use": [{"tool": "Bandit", "priority": 1}]
        }

        db.store_ai_analysis(scan_id, test_analysis)

        # Update scan run
        db.update_scan_run(scan_id, "completed", 1, {"ERROR": 1}, 5.2)

        # Test retrieval
        scan_data = db.get_scan_run(scan_id)
        findings = db.get_scan_findings(scan_id)
        analysis = db.get_ai_analysis(scan_id)
        summary = db.get_scan_summary()

        print("\n" + "="*50)
        print("DATABASE TEST RESULTS")
        print("="*50)
        print(f"Scan Run: {scan_data}")
        print(f"Findings: {len(findings)} found")
        print(f"Analysis: {analysis['executive_summary'] if analysis else 'None'}")
        print(f"Summary: {summary}")

        # Clean up test database
        os.remove("test_watchman.db")
        print("✓ Database handler test completed successfully")

    except Exception as e:
        print(f"Database test failed: {e}")
        import traceback
        traceback.print_exc()
