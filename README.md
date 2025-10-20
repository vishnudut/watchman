# Watchman 🛡️

An intelligent, autonomous security scanning platform that automatically detects vulnerabilities in GitHub repositories using AI-powered analysis.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-FF9900?style=flat&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/bedrock/)
[![Claude 3.5](https://img.shields.io/badge/Claude-3.5_Haiku-5A67D8?style=flat)](https://www.anthropic.com/claude)

## Overview

Watchman revolutionizes application security by automating vulnerability detection and providing intelligent, AI-powered analysis. Instead of drowning developers in false positives, Watchman delivers actionable insights with business context, automated GitHub issue creation, and executive summaries for stakeholders.

### Key Features

- **Autonomous Scanning**: Automatic security scans triggered by GitHub webhooks
- **AI-Powered Analysis**: AWS Bedrock with Claude 3.5 analyzes findings with business context
- **Smart Filtering**: 75% reduction in false positives through intelligent relevance scoring
- **GitHub Integration**: Automatic issue creation with detailed remediation steps
- **Real-time Dashboard**: Live monitoring and visualization of security metrics
- **Sub-60 Second Processing**: From code push to security issue creation
- **Loop Prevention**: Intelligent detection to prevent infinite scanning cycles

## Architecture

```
┌─────────────────────┐
│   GitHub Webhook    │
│   (Push Events)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   FastAPI Backend   │
│   ┌─────────────┐   │
│   │Orchestrator │   │──────┐
│   └─────────────┘   │      │
└──────────┬──────────┘      │
           │                  │
    ┌──────┴──────┐          │
    ▼             ▼          ▼
┌─────────┐  ┌──────────┐  ┌────────────┐
│ Semgrep │  │   AWS    │  │  GitHub    │
│ Scanner │  │ Bedrock  │  │    API     │
│         │  │(Claude)  │  │            │
└─────────┘  └──────────┘  └────────────┘
    │             │              │
    └─────────┬───┴──────────────┘
              ▼
      ┌──────────────┐
      │   Database   │
      │   (SQLite)   │
      └──────────────┘
              │
              ▼
      ┌──────────────┐
      │  Next.js UI  │
      │  Dashboard   │
      └──────────────┘
```

### Component Overview

#### Backend Services

- **Orchestrator** (`orchestrator.py`): Central coordinator managing the complete workflow
- **Security Scanner** (`scanner.py`): Semgrep integration for static analysis
- **Bedrock Agent** (`bedrock_agent.py`): AWS Bedrock/Claude 3.5 for AI analysis
- **GitHub Handler** (`github_handler.py`): Repository management and issue creation
- **Database** (`database.py`): SQLite for scan results and metrics
- **Email Handler** (`email_handler.py`): Stakeholder notifications
- **Vanta Handler** (`vanta_handler.py`): Compliance reporting

#### Frontend

- **Next.js 14** with App Router
- **TailwindCSS** for styling
- **Real-time** scan monitoring
- **Interactive** data visualization

## Tech Stack

### Backend
- **FastAPI** - High-performance async API framework
- **Semgrep** - Static analysis security scanner
- **AWS Bedrock** - Enterprise AI infrastructure
- **Claude 3.5 Haiku** - AI model for intelligent analysis
- **PyGithub** - GitHub API integration
- **SQLite** - Lightweight database
- **Boto3** - AWS SDK

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **TailwindCSS** - Utility-first CSS
- **Lucide React** - Icon system
- **Chart.js** - Data visualization

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- Git
- Semgrep
- AWS account with Bedrock access
- GitHub account and Personal Access Token

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/watchman.git
   cd watchman
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Environment Configuration**

   Create `backend/.env`:
   ```env
   # AWS Bedrock (Required)
   BEDROCK_AGENTCORE_API_KEY=your_bedrock_api_key
   AWS_REGION=us-east-1
   AWS_BEARER_TOKEN_BEDROCK=your_bearer_token

   # GitHub Integration (Required)
   GITHUB_TOKEN=ghp_your_github_token

   # Optional: Fallback Direct API
   ANTHROPIC_API_KEY=sk-ant-your_key

   # Optional: Email Notifications
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_FROM=security@yourcompany.com
   EMAIL_PASSWORD=your_password

   # Database
   DATABASE_PATH=./watchman.db
   ```

### Running the Application

#### Development Mode

**Backend** (Terminal 1):
```bash
cd backend
source venv/bin/activate
python main.py
# Server runs on http://localhost:8000
```

**Frontend** (Terminal 2):
```bash
cd frontend
npm run dev
# Dashboard available at http://localhost:3000
```

### Setting Up GitHub Webhooks

1. Go to your repository **Settings** → **Webhooks** → **Add webhook**
2. Set **Payload URL**: `https://your-domain.com/webhook/github`
3. Set **Content type**: `application/json`
4. Select events: **Push events**
5. Add webhook

## API Endpoints

### Core Endpoints

```
GET  /                    # API information
GET  /health              # Health check
POST /webhook/github      # GitHub webhook handler
POST /scan/manual         # Trigger manual scan
GET  /scan/{scan_id}      # Get scan status
GET  /scans               # List recent scans
GET  /stats               # System statistics
```

### Example: Manual Scan

```bash
curl -X POST http://localhost:8000/scan/manual \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "owner/repository",
    "branch": "main"
  }'
```

### Example: Get Recent Scans

```bash
curl http://localhost:8000/scans?limit=10
```

## Workflow

1. **Trigger**: Developer pushes code to GitHub
2. **Webhook**: GitHub sends push event to Watchman
3. **Clone**: Repository is cloned locally
4. **Scan**: Semgrep analyzes code with security rulesets
5. **AI Analysis**: AWS Bedrock/Claude evaluates findings
6. **Prioritization**: Vulnerabilities scored by severity and context
7. **Issue Creation**: GitHub issues created with remediation steps
8. **Notification**: Email summaries sent to stakeholders
9. **Persistence**: Results stored in database

**Total Time**: < 60 seconds

## Security Rulesets

Watchman uses curated Semgrep rulesets:

- `p/security-audit` - General security issues
- `p/owasp-top-ten` - OWASP Top 10 vulnerabilities
- `p/cwe-top-25` - CWE Top 25 dangerous errors

## Loop Prevention

Watchman includes intelligent loop prevention:

- **Branch Filtering**: Skips branches starting with `security-fixes-`
- **Commit Message Filtering**: Ignores commits starting with `security:`
- **Idempotency**: Prevents duplicate processing of same commit

## Database Schema

### scan_runs
```sql
CREATE TABLE scan_runs (
    id INTEGER PRIMARY KEY,
    repo_name TEXT NOT NULL,
    branch TEXT NOT NULL,
    commit_sha TEXT NOT NULL,
    scan_status TEXT DEFAULT 'pending',
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    scan_duration_seconds REAL,
    scan_timestamp DATETIME,
    created_at DATETIME,
    updated_at DATETIME
);
```

### security_findings
```sql
CREATE TABLE security_findings (
    id INTEGER PRIMARY KEY,
    scan_run_id INTEGER,
    rule_id TEXT,
    severity TEXT,
    file_path TEXT,
    line_number INTEGER,
    message TEXT,
    fix_suggestion TEXT,
    FOREIGN KEY (scan_run_id) REFERENCES scan_runs(id)
);
```

## Configuration

### Semgrep Rules

Customize in `scanner.py`:
```python
self.rules = [
    "p/security-audit",
    "p/owasp-top-ten",
    "p/cwe-top-25",
    # Add custom rules here
]
```

### AI Model Selection

Configure in `bedrock_agent.py`:
```python
modelId = "anthropic.claude-3-5-haiku-20241022-v1:0"
# Options: claude-3-5-haiku, claude-3-5-sonnet, claude-opus
```


## Performance Metrics

- **Average Scan Time**: 25 seconds
- **AI Analysis Time**: 15 seconds
- **False Positive Reduction**: 75%
- **Webhook Response Time**: <200ms
- **Database Query Time**: <50ms


## Roadmap

### Near-term
- [ ] Multi-language support (JavaScript, Go, Rust)
- [ ] Slack/Teams integration
- [ ] Custom rule creation UI
- [ ] Advanced filtering and search

### Medium-term
- [ ] ML-based vulnerability prioritization
- [ ] Kubernetes deployment configs
- [ ] Enterprise SSO integration
- [ ] Advanced analytics dashboard

### Long-term
- [ ] Autonomous fix generation with PRs
- [ ] Security tool marketplace
- [ ] Compliance reporting (SOC2, ISO 27001)
- [ ] Multi-cloud deployment support

---
Making security delightful, one scan at a time.
