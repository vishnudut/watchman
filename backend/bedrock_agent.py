import json
import os
from typing import Dict, List, Any
from dotenv import load_dotenv
import requests

load_dotenv()


class BedrockAgentCore:
    """
    Anthropic Claude API client for orchestrating security analysis
    Direct API integration replacing AWS Bedrock for faster development
    """

    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in .env")

        # API configuration
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-5-haiku-20241022"
        self.max_tokens = 4000

        print(f"✓ Claude API client initialized with model: {self.model}")

        # Test connection
        self._test_connection()

    def _test_connection(self):
        """Test if the Claude API is working"""
        try:
            response = self._call_claude_api("Hello, can you confirm you're working?")

            if response and "content" in response:
                print("✓ Claude API connection successful!")
            else:
                print("⚠️ Unexpected response format from Claude API")

        except Exception as e:
            print(f"⚠️ Claude API connection test failed: {e}")

    def analyze_security_findings(
        self,
        scan_results: Dict,
        repo_context: Dict,
        available_tools: List[Dict] = None
    ) -> Dict:
        """
        Use Claude to analyze security findings and decide actions

        Args:
            scan_results: Output from Semgrep scanner
            repo_context: Repository metadata (name, branch, commit)
            available_tools: List of tools the agent can use (optional)

        Returns:
            Agent's analysis and recommended actions
        """
        print("🤖 Starting Claude security analysis...")

        if available_tools is None:
            available_tools = []

        try:
            # Build the analysis prompt
            prompt = self._build_analysis_prompt(scan_results, repo_context, available_tools)

            # Call Claude API
            response = self._call_claude_api(prompt)

            # Parse the response
            analysis = self._parse_claude_response(response)

            print("✓ Claude security analysis complete")
            return analysis

        except Exception as e:
            print(f"❌ Claude analysis error: {e}")
            # Fallback to basic analysis
            return self._fallback_analysis(scan_results, repo_context)

    def _call_claude_api(self, prompt: str) -> Dict:
        """Make API call to Anthropic Claude"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )

            # Print detailed error info for debugging
            if response.status_code != 200:
                print(f"❌ Claude API Error {response.status_code}")
                print(f"Request payload: {json.dumps(payload, indent=2)}")
                print(f"Response: {response.text}")

            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            print(f"❌ Detailed error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response text: {e.response.text}")
            raise Exception(f"Claude API call failed: {e}")

    def _build_analysis_prompt(self, scan_results: Dict, repo_context: Dict, available_tools: List[Dict]) -> str:
        """Build the analysis prompt for Claude"""

        context = self._build_analysis_context(scan_results, repo_context)

        tools_list = ""
        if available_tools:
            tools_list = f"\nAvailable tools: {', '.join([tool.get('name', 'unknown') for tool in available_tools])}"

        prompt = f"""You are a senior DevSecOps security analyst. Analyze the following security scan results and provide actionable recommendations.

{context}
{tools_list}

Please provide your analysis in JSON format with this exact structure:
{{
    "executive_summary": "2-3 sentence summary of findings",
    "critical_issues": [
        {{
            "title": "Short descriptive title",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "file": "file path",
            "line": line_number,
            "description": "Clear description of the vulnerability",
            "business_impact": "Business impact explanation",
            "recommended_fix": "Specific code fix recommendation",
            "compliance_mapping": ["OWASP", "SOC 2", "etc"]
        }}
    ],
    "recommended_actions": [
        "Prioritized list of actions to take"
    ],
    "tools_to_use": [
        {{"tool": "tool_name", "priority": 1}}
    ]
}}

Focus on:
1. The most critical security issues (top 3)
2. Actionable, developer-friendly recommendations
3. Business impact and compliance implications
4. Specific code fixes where possible

Respond ONLY with the JSON - no additional text or formatting."""

        return prompt

    def _build_analysis_context(self, scan_results: Dict, repo_context: Dict) -> str:
        """Build context string for analysis"""
        critical_issues = scan_results.get('by_severity', {}).get('ERROR', [])
        warnings = scan_results.get('by_severity', {}).get('WARNING', [])

        context = f"""
Repository Information:
- Name: {repo_context.get('repo_name', 'Unknown')}
- Branch: {repo_context.get('branch', 'main')}
- Commit: {repo_context.get('commit_sha', 'N/A')[:8]}

Scan Results Summary:
- Total Findings: {scan_results.get('total_findings', 0)}
- Critical (ERROR): {len(critical_issues)}
- Warnings: {len(warnings)}
- Info: {len(scan_results.get('by_severity', {}).get('INFO', []))}

Critical Security Issues:
{json.dumps(critical_issues, indent=2)}

Top Warnings (first 5):
{json.dumps(warnings[:5], indent=2)}
"""
        return context

    def _parse_claude_response(self, response: Dict) -> Dict:
        """Parse Claude response into structured format"""
        try:
            # Extract the response text from Claude response format
            if "content" in response and len(response["content"]) > 0:
                response_text = response["content"][0]["text"]
            else:
                raise ValueError("No content in response")

            # Try to parse as JSON
            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from the text
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    # Fallback: create structure from text
                    analysis = {
                        "executive_summary": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                        "critical_issues": [],
                        "recommended_actions": ["Review the analysis text"],
                        "tools_to_use": []
                    }

            # Validate structure
            required_keys = ["executive_summary", "critical_issues", "recommended_actions", "tools_to_use"]
            for key in required_keys:
                if key not in analysis:
                    analysis[key] = [] if key != "executive_summary" else "Analysis completed"

            analysis["raw_response"] = response_text
            return analysis

        except Exception as e:
            print(f"⚠️ Error parsing Claude response: {e}")
            return self._fallback_response(response)

    def _fallback_response(self, response: Dict) -> Dict:
        """Create a fallback response structure"""
        return {
            "executive_summary": "Claude response could not be parsed",
            "critical_issues": [],
            "recommended_actions": ["Review raw Claude output"],
            "tools_to_use": [],
            "raw_response": str(response)
        }

    def _fallback_analysis(self, scan_results: Dict, repo_context: Dict) -> Dict:
        """Fallback analysis when Claude is unavailable"""
        print("🔄 Using fallback analysis...")

        critical_count = len(scan_results.get('by_severity', {}).get('ERROR', []))
        warning_count = len(scan_results.get('by_severity', {}).get('WARNING', []))

        # Create basic analysis from scan results
        critical_issues = []
        for issue in scan_results.get('by_severity', {}).get('ERROR', [])[:3]:
            critical_issues.append({
                "title": issue.get('rule_id', 'Security Issue'),
                "severity": "CRITICAL",
                "file": issue.get('file', 'unknown'),
                "line": issue.get('line', 0),
                "description": issue.get('message', 'Security vulnerability detected'),
                "business_impact": "Potential security risk requiring immediate attention",
                "recommended_fix": "Review and remediate the identified security issue according to best practices",
                "compliance_mapping": ["OWASP", "SOC 2"]
            })

        return {
            "executive_summary": f"Automated fallback analysis: Found {critical_count} critical issues and {warning_count} warnings requiring attention.",
            "critical_issues": critical_issues,
            "recommended_actions": [
                "Review all critical security findings",
                "Implement recommended security fixes",
                "Run additional security tests",
                "Consider manual security review"
            ],
            "tools_to_use": [
                {"tool": "create_github_issue", "priority": 1},
                {"tool": "log_to_vanta", "priority": 2}
            ]
        }


if __name__ == "__main__":
    # Test the Claude API integration
    try:
        agent = BedrockAgentCore()

        # Mock scan results for testing
        test_scan = {
            "total_findings": 2,
            "by_severity": {
                "ERROR": [
                    {
                        "rule_id": "sql-injection",
                        "message": "Potential SQL injection vulnerability detected in user input handling",
                        "file": "app.py",
                        "line": 45,
                        "code_snippet": "cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')"
                    }
                ],
                "WARNING": [
                    {
                        "rule_id": "weak-crypto",
                        "message": "Weak cryptographic algorithm detected",
                        "file": "auth.py",
                        "line": 23
                    }
                ],
                "INFO": []
            }
        }

        test_repo = {
            "repo_name": "test-security-app",
            "branch": "main",
            "commit_sha": "abc123def456"
        }

        # Test the analysis
        result = agent.analyze_security_findings(test_scan, test_repo, [])
        print("\n" + "="*50)
        print("ANALYSIS RESULTS")
        print("="*50)
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
