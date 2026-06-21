# Google Chat AI Agent - Complete Implementation Plan

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Phase 1: Bitbucket Code Agent](#3-phase-1-bitbucket-code-agent)
4. [Phase 2: Jira Integration](#4-phase-2-jira-integration)
5. [Google Chat Integration](#5-google-chat-integration)
6. [API Keys & Secrets](#6-api-keys--secrets)
7. [Project Structure](#7-project-structure)
8. [Dependencies](#8-dependencies)
9. [Deployment](#9-deployment)
10. [Testing Strategy](#10-testing-strategy)

---

## 1. Project Overview

### What This Agent Does

A Google Chat bot that acts as an AI-powered software engineering assistant. When mentioned in a chat space, it can:

**Phase 1 - Code Agent:**
- Analyze Bitbucket repositories (code structure, branches, PRs, commits)
- Understand codebase context before making changes
- Implement features based on natural language instructions
- Create branches, make changes, and open Pull Requests automatically
- Answer questions about code structure, patterns, and architecture

**Phase 2 - Jira Integration:**
- Query Jira for issue status, sprint boards, and backlog items
- Brainstorm features using project context + Jira data
- Provide summaries of team workload, blockers, and priorities
- Link code changes to Jira tickets

### Target Users

- Developers who want quick code analysis or feature implementation
- Product managers who need Jira status updates and brainstorming
- Team leads who want a bird's-eye view of project health

---

## 2. Architecture

### High-Level Architecture

```
┌─────────────────────┐
│   Google Chat Space  │
└─────────┬───────────┘
          │ Webhook
          ▼
┌─────────────────────┐
│   Chat Bot Server   │  ← Receives messages, routes to agent
│   (FastAPI/Express) │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Agent Core (LLM)  │  ← OpenAI / Claude / local model
│   + Tool Router     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────────────┐
│                   Tool Layer                     │
├──────────────┬──────────────┬───────────────────┤
│  Bitbucket   │    Jira      │   Git Operations  │
│  API Client  │  API Client  │   (local clone)   │
└──────────────┴──────────────┴───────────────────┘
```

### Component Breakdown

| Component | Purpose | Technology |
|-----------|---------|------------|
| Chat Server | Receives Google Chat webhooks, sends replies | Python (FastAPI) or Node.js (Express) |
| Agent Core | LLM orchestration, tool calling, reasoning | LangChain / OpenAI SDK / Anthropic SDK |
| Bitbucket Client | Repo analysis, branch management, PR creation | Bitbucket REST API v2.0 |
| Jira Client | Issue queries, board data, sprint info | Jira REST API v3 |
| Git Operations | Local repo cloning, code edits, commits | GitPython / simple-git |
| Prompt Store | System prompts, few-shot examples | YAML/JSON files or database |

### Message Flow

```
User: "@Bot analyze the auth module in backend repo"
  │
  ▼
Google Chat → Webhook → Bot Server
  │
  ▼
Bot Server → Parse message, extract intent
  │
  ▼
Agent Core → Decide: Use Bitbucket tools
  │
  ▼
Tool: Bitbucket API → List repos → Find "backend" repo
  │
  ▼
Tool: Bitbucket API → Get file tree → Identify auth module
  │
  ▼
Tool: Bitbucket API → Read file contents → auth.py, auth_controller.py
  │
  ▼
Agent Core → Synthesize analysis → Return structured response
  │
  ▼
Bot Server → Send reply to Google Chat thread
```

---

## 3. Phase 1: Bitbucket Code Agent

### 3.1 Capabilities

#### 3.1.1 Code Analysis
- Read repository file trees and understand project structure
- Parse README, package.json, requirements.txt, etc.
- Identify tech stack, frameworks, and patterns
- Analyze code quality (linting, type hints, test coverage)
- Understand directory conventions (MVC, feature-based, etc.)

#### 3.1.2 Code Understanding
- Read and understand specific files on demand
- Trace function calls and dependencies
- Identify related tests, configs, and documentation
- Understand database schemas and API contracts

#### 3.1.3 Feature Implementation
- Create feature branches from the default branch
- Implement code changes based on natural language instructions
- Write corresponding tests
- Update documentation if needed
- Create Pull Request with description and diff summary
- Link PR to Jira ticket (if ticket ID provided)

#### 3.1.4 Code Review & Feedback
- Review existing PRs for quality and issues
- Suggest improvements and optimizations
- Identify potential bugs or security concerns

### 3.2 Bitbucket API Integration

#### Authentication
```
BITBUCKET_WORKSPACE=your-workspace
BITBUCKET_USERNAME=your-username
BITBUCKET_APP_PASSWORD=your-app-password
BITBUCKET_REPO_SLUG=target-repo
```

#### Key API Endpoints Used

| Operation | Endpoint | Purpose |
|-----------|----------|---------|
| List repos | `GET /2.0/repositories/{workspace}` | Discover available repos |
| Get repo info | `GET /2.0/repositories/{workspace}/{repo_slug}` | Repo metadata |
| File tree | `GET /2.0/repositories/{workspace}/{repo_slug}/src/{branch}` | Browse code |
| Read file | `GET /2.0/repositories/{workspace}/{repo_slug}/src/{branch}/{path}` | Read source |
| Create branch | `POST /2.0/repositories/{workspace}/{repo_slug}/refs/branches` | Branch for work |
| Commit changes | `POST /2.0/repositories/{workspace}/{repo_slug}/src` | Push code |
| Create PR | `POST /2.0/repositories/{workspace}/{repo_slug}/pullrequests` | Open PR |
| List PRs | `GET /2.0/repositories/{workspace}/{repo_slug}/pullrequests` | Review PRs |
| Get diff | `GET /2.0/repositories/{workspace}/{repo_slug}/pullrequests/{id}/diff` | Review changes |

### 3.3 Tool Definitions for Agent

```python
tools = [
    {
        "name": "list_repositories",
        "description": "List all repositories in the workspace",
        "parameters": {"workspace": "string"}
    },
    {
        "name": "get_file_tree",
        "description": "Get the directory structure of a repository branch",
        "parameters": {
            "repo_slug": "string",
            "branch": "string (default: main)",
            "path": "string (optional, subdirectory)"
        }
    },
    {
        "name": "read_file",
        "description": "Read the contents of a specific file in the repository",
        "parameters": {
            "repo_slug": "string",
            "branch": "string",
            "file_path": "string"
        }
    },
    {
        "name": "search_code",
        "description": "Search for code patterns across the repository",
        "parameters": {
            "repo_slug": "string",
            "query": "string",
            "file_pattern": "string (optional)"
        }
    },
    {
        "name": "create_branch",
        "description": "Create a new branch from a source branch",
        "parameters": {
            "repo_slug": "string",
            "branch_name": "string",
            "source_branch": "string (default: main)"
        }
    },
    {
        "name": "commit_and_push",
        "description": "Commit changes and push to a branch",
        "parameters": {
            "repo_slug": "string",
            "branch": "string",
            "files": "list of {path, content}",
            "commit_message": "string"
        }
    },
    {
        "name": "create_pull_request",
        "description": "Create a PR for the branch",
        "parameters": {
            "repo_slug": "string",
            "source_branch": "string",
            "destination_branch": "string",
            "title": "string",
            "description": "string",
            "reviewers": "list of strings (optional)"
        }
    },
    {
        "name": "get_pr_diff",
        "description": "Get the diff of a pull request",
        "parameters": {
            "repo_slug": "string",
            "pr_id": "integer"
        }
    },
    {
        "name": "analyze_repo_structure",
        "description": "Comprehensive analysis of repo structure, tech stack, patterns",
        "parameters": {
            "repo_slug": "string",
            "branch": "string"
        }
    }
]
```

### 3.4 Implementation Workflow: Feature Development

```
User: "Implement a password reset feature in the auth module"

Agent Steps:
1. CLONE/UPDATE
   - Clone repo (or pull latest) to local workspace
   - Identify the target branch (main/develop)

2. ANALYZE
   - Read auth module files
   - Understand existing auth patterns
   - Check for existing password handling
   - Review database schema

3. PLAN
   - Break feature into steps:
     a. Add reset token generation
     b. Create reset endpoint
     c. Add email sending (if applicable)
     d. Create frontend form (if applicable)
     e. Write tests

4. IMPLEMENT
   - Create feature branch: feature/password-reset
   - Write code changes file by file
   - Follow existing code patterns and conventions

5. TEST
   - Write unit tests for new functionality
   - Run existing tests to ensure no regressions

6. PR
   - Create PR with:
     - Clear title: "feat: add password reset functionality"
     - Description with changes summary
     - Link to Jira ticket (if provided)
     - Request reviewers

7. REPORT
   - Send PR link to Google Chat
   - Summarize what was implemented
```

---

## 4. Phase 2: Jira Integration

### 4.1 Capabilities

#### 4.1.1 Status Queries
- "What's the status of PROJ-123?"
- "Show me all tickets in the current sprint"
- "What's in the backlog for Project X?"
- "How many tickets are blocked?"

#### 4.1.2 Board Overview
- "Give me a summary of the sprint board"
- "What are the high priority items?"
- "Show me tickets assigned to John"

#### 4.1.3 Brainstorming with Context
- "Based on our backlog, what features should we prioritize?"
- "Brainstorm improvements for the authentication system"
- "What's the effort estimate for adding SSO?"

#### 4.1.4 Code-to-Jira Linking
- Link commits to tickets automatically
- Update ticket status from chat
- Add PR links to ticket comments

### 4.2 Jira API Integration

#### Authentication
```
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJ
```

#### Key API Endpoints Used

| Operation | Endpoint | Purpose |
|-----------|----------|---------|
| Get issue | `GET /rest/api/3/issue/{issueKey}` | Single ticket details |
| Search issues | `POST /rest/api/3/search` (JQL) | Query tickets |
| Get board | `GET /rest/agile/1.0/board/{boardId}` | Board info |
| Get sprint | `GET /rest/agile/1.0/board/{boardId}/sprint/{sprintId}` | Sprint details |
| Get backlog | `GET /rest/agile/1.0/board/{boardId}/backlog` | Backlog items |
| Update issue | `PUT /rest/api/3/issue/{issueKey}` | Modify ticket |
| Add comment | `POST /rest/api/3/issue/{issueKey}/comment` | Comment on ticket |
| Get transitions | `GET /rest/api/3/issue/{issueKey}/transitions` | Available status changes |
| Transition | `POST /rest/api/3/issue/{issueKey}/transitions` | Change status |

### 4.3 Tool Definitions for Agent

```python
tools = [
    {
        "name": "get_jira_issue",
        "description": "Get details of a Jira issue",
        "parameters": {
            "issue_key": "string (e.g., PROJ-123)"
        }
    },
    {
        "name": "search_jira_issues",
        "description": "Search Jira issues using JQL query",
        "parameters": {
            "jql": "string",
            "max_results": "integer (default: 20)"
        }
    },
    {
        "name": "get_sprint_board",
        "description": "Get current sprint board overview",
        "parameters": {
            "board_id": "integer"
        }
    },
    {
        "name": "get_backlog",
        "description": "Get all items in the project backlog",
        "parameters": {
            "project_key": "string",
            "limit": "integer (default: 50)"
        }
    },
    {
        "name": "get_sprint_status",
        "description": "Get status of current/last sprint",
        "parameters": {
            "board_id": "integer"
        }
    },
    {
        "name": "update_issue_status",
        "description": "Transition a Jira issue to a new status",
        "parameters": {
            "issue_key": "string",
            "target_status": "string"
        }
    },
    {
        "name": "add_issue_comment",
        "description": "Add a comment to a Jira issue",
        "parameters": {
            "issue_key": "string",
            "comment_body": "string"
        }
    },
    {
        "name": "brainstorm_with_context",
        "description": "Analyze project context and brainstorm feature ideas",
        "parameters": {
            "project_key": "string",
            "context": "string (additional instructions)"
        }
    }
]
```

### 4.4 Brainstorming Workflow

```
User: "What features should we build next based on our backlog?"

Agent Steps:
1. FETCH DATA
   - Get all backlog items (stories, bugs, tech debt)
   - Get current sprint status (what's done, what's in progress)
   - Get recent PRs from Bitbucket (what code is changing)

2. ANALYZE
   - Categorize: new features, bugs, tech debt, improvements
   - Identify patterns: recurring bug types, performance issues
   - Cross-reference: which features have code support, which don't
   - Calculate: story point distribution, velocity trends

3. SYNTHESIZE
   - Identify high-impact items (frequent bugs + low effort)
   - Suggest feature combinations (related tickets that could be grouped)
   - Recommend priorities based on:
     a. Business impact (from Jira priority field)
     b. Technical debt (oldest items, most comments)
     c. Dependencies (blocking items)
     d. Code complexity (from Bitbucket analysis)

4. PRESENT
   - Structured recommendation with reasoning
   - Link to relevant Jira tickets
   - Code context from Bitbucket analysis
   - Effort estimates where available
```

---

## 5. Google Chat Integration

### 5.1 Setup Requirements

1. **Google Cloud Console**
   - Create a project
   - Enable Google Chat API
   - Create Service Account credentials
   - Set up OAuth if needed

2. **Google Chat Space**
   - Add bot to the target space
   - Configure bot permissions (read/write messages)

3. **Webhook Configuration**
   - Set up receiving webhook URL
   - Configure event subscriptions (message received, bot added)

### 5.2 Message Handling

```python
# Event types to handle
events = [
    "MESSAGE_RECEIVED",      # User sends a message
    "ADDED_TO_SPACE",        # Bot added to a space
    "REMOVED_FROM_SPACE",    # Bot removed from a space
    "CARD_CLICKED",          # User clicks on a card action
    "BOT_ADDED",             # Bot added to space (alternate)
]

# Message routing
def handle_message(event):
    message = event.get("message", {})
    text = message.get("text", "")
    space_id = message.get("space", {}).get("name", "")

    # Extract mentions
    mentions = message.get("annotations", [])

    # Route based on content
    if "@" in text:
        return process_agent_command(text, space_id)
    return None
```

### 5.3 Response Format

```python
# Simple text response
response = {
    "text": "Analysis complete. Found 3 files in auth module."
}

# Rich card response
response = {
    "cardsV2": [{
        "cardId": "analysis-result",
        "card": {
            "header": {
                "title": "Repository Analysis: backend-api",
                "subtitle": "Auth Module Review"
            },
            "sections": [{
                "header": "Structure",
                "widgets": [{
                    "decoratedText": {
                        "topLabel": "Files Found",
                        "text": "5 files in auth/"
                    }
                }]
            }, {
                "header": "PR Created",
                "widgets": [{
                    "buttonList": {
                        "buttons": [{
                            "text": "View PR",
                            "onClick": {
                                "openLink": {
                                    "url": "https://bitbucket.org/..."
                                }
                            }
                        }]
                    }
                }]
            }]
        }
    }]
}
```

### 5.4 Bot Commands

| Command | Action | Example |
|---------|--------|---------|
| `analyze <repo>` | Analyze repo structure | `analyze backend-api` |
| `read <repo> <file>` | Read specific file | `read backend-api src/auth.py` |
| `implement <feature>` | Implement a feature | `implement password reset in auth` |
| `pr list` | List open PRs | `pr list` |
| `pr review <id>` | Review a PR | `pr review 123` |
| `jira status <ticket>` | Get ticket status | `jira status PROJ-123` |
| `jira sprint` | Current sprint overview | `jira sprint` |
| `jira backlog` | Show backlog | `jira backlog` |
| `brainstorm <topic>` | Brainstorm features | `brainstorm authentication improvements` |
| `help` | Show available commands | `help` |

---

## 6. API Keys & Secrets

### Required Secrets

```bash
# .env file
# Google Chat
GOOGLE_SERVICE_ACCOUNT_KEY=path/to/service-account.json
GOOGLE_CHAT_SPACE_ID=spaces/XXXXX

# Bitbucket
BITBUCKET_WORKSPACE=your-workspace
BITBUCKET_USERNAME=your-username
BITBUCKET_APP_PASSWORD=your-app-password

# Jira
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token

# LLM Provider
OPENAI_API_KEY=sk-...           # or
ANTHROPIC_API_KEY=sk-ant-...    # or
LOCAL_MODEL_ENDPOINT=http://localhost:11434

# Database (for caching/conversation history)
DATABASE_URL=postgresql://user:pass@localhost:5432/agent_db
```

### Security Notes

- Never commit `.env` files
- Use environment variables in production
- Rotate API tokens periodically
- Use least-privilege access for Bitbucket/Jira tokens
- Store service account keys securely (not in repo)

---

## 7. Project Structure

```
agent-google-chat/
├── doc/
│   └── implementation-plan.md    ← This file
├── src/
│   ├── main.py                   ← Entry point, server startup
│   ├── config.py                 ← Configuration loading
│   ├── server/
│   │   ├── __init__.py
│   │   ├── app.py                ← FastAPI/Express app
│   │   ├── routes.py             ← Webhook endpoints
│   │   └── middleware.py         ← Auth, logging
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── core.py               ← Agent orchestration
│   │   ├── prompts.py            ← System prompts
│   │   ├── parser.py             ← Message parsing/routing
│   │   └── memory.py             ← Conversation context
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── bitbucket/
│   │   │   ├── __init__.py
│   │   │   ├── client.py         ← Bitbucket API client
│   │   │   ├── repo_tools.py     ← Repo analysis tools
│   │   │   ├── pr_tools.py       ← PR creation/review tools
│   │   │   └── code_tools.py     ← File read/write tools
│   │   ├── jira/
│   │   │   ├── __init__.py
│   │   │   ├── client.py         ← Jira API client
│   │   │   ├── issue_tools.py    ← Issue query tools
│   │   │   └── board_tools.py    ← Sprint/board tools
│   │   └── git/
│   │       ├── __init__.py
│   │       └── local.py          ← Local git operations
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── google_chat.py        ← Google Chat API client
│   │   └── card_builder.py       ← Rich message builder
│   └── utils/
│       ├── __init__.py
│       ├── logger.py             ← Logging setup
│       └── rate_limiter.py       ← API rate limiting
├── tests/
│   ├── test_agent.py
│   ├── test_bitbucket.py
│   ├── test_jira.py
│   └── test_chat.py
├── prompts/
│   ├── system.md                 ← Base system prompt
│   ├── code_analysis.md          ← Code analysis prompt
│   ├── feature_impl.md           ← Feature implementation prompt
│   └── brainstorming.md          ← Brainstorming prompt
├── .env.example                  ← Environment template
├── .gitignore
├── requirements.txt              ← Python dependencies
├── Dockerfile                    ← Container deployment
├── docker-compose.yml            ← Local dev setup
└── README.md                     ← Usage instructions
```

---

## 8. Dependencies

### Python Packages

```txt
# requirements.txt
# Web Server
fastapi==0.109.0
uvicorn==0.27.0
python-multipart==0.0.6

# LLM
openai==1.12.0                 # OpenAI API
anthropic==0.18.0              # Anthropic API (alternative)
langchain==0.1.0               # Agent framework (optional)
langchain-openai==0.0.5        # LangChain + OpenAI

# API Clients
httpx==0.27.0                  # HTTP client
requests==2.31.0               # Alternative HTTP client

# Bitbucket
python-bitbucket==0.0.1        # Bitbucket client (or use httpx directly)

# Jira
jira==3.8.0                    # Jira client (or use httpx directly)

# Git
gitpython==3.1.41              # Git operations

# Utilities
python-dotenv==1.0.0           # Env file loading
pydantic==2.6.0                # Data validation
pydantic-settings==2.1.0       # Settings management

# Database (optional)
sqlalchemy==2.0.25             # ORM
asyncpg==0.29.0                # PostgreSQL async

# Testing
pytest==8.0.0
pytest-asyncio==0.23.0
```

### System Requirements

- Python 3.11+
- Git (for local repo operations)
- Docker (optional, for deployment)

---

## 9. Deployment

### Option 1: Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  agent:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./repos:/app/repos    # Persist cloned repos
    restart: unless-stopped
```

### Option 2: Cloud Run (GCP)

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/chat-agent
gcloud run deploy chat-agent \
  --image gcr.io/PROJECT_ID/chat-agent \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars-file .env
```

### Option 3: VM / VPS

```bash
# Setup
sudo apt update && sudo apt install python3.11 git
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with systemd
sudo cp agent.service /etc/systemd/system/
sudo systemctl enable agent
sudo systemctl start agent
```

### Webhook Setup

After deployment, configure Google Chat webhook:

1. Go to Google Chat API → Configuration
2. Set bot name and avatar
3. Enter webhook URL: `https://your-domain.com/webhook/google-chat`
4. Enable bot in target spaces

---

## 10. Testing Strategy

### Unit Tests

```python
# tests/test_bitbucket.py
import pytest
from src.tools.bitbucket.client import BitbucketClient

@pytest.fixture
def client():
    return BitbucketClient(
        workspace="test-workspace",
        username="test-user",
        app_password="test-pass"
    )

async def test_list_repos(client):
    repos = await client.list_repositories()
    assert len(repos) > 0
    assert all("slug" in repo for repo in repos)

async def test_read_file(client):
    content = await client.read_file(
        repo="test-repo",
        branch="main",
        path="README.md"
    )
    assert content is not None
```

### Integration Tests

```python
# tests/test_agent_integration.py
async def test_full_feature_workflow():
    """Test: analyze → implement → PR flow"""
    agent = create_agent()

    result = await agent.process(
        "Analyze the auth module in backend-api and implement a password reset"
    )

    assert result.status == "success"
    assert result.pr_url is not None
```

### Manual Testing Checklist

- [ ] Bot receives messages in Google Chat
- [ ] Bot responds to basic commands (`help`, `status`)
- [ ] Bitbucket authentication works
- [ ] Can list and read repository files
- [ ] Can create branches and commits
- [ ] Can create Pull Requests
- [ ] Jira authentication works
- [ ] Can query issues and sprints
- [ ] Can update issue status
- [ ] Rich card responses render correctly
- [ ] Error handling works (invalid repo, missing permissions)
- [ ] Rate limiting doesn't break normal usage
- [ ] Conversation context persists within a thread

---

## Implementation Priority

### Week 1-2: Foundation
- [ ] Project setup and structure
- [ ] Google Chat webhook server
- [ ] Basic message parsing and routing
- [ ] Agent core with LLM integration

### Week 3-4: Bitbucket Core
- [ ] Bitbucket API client
- [ ] Repo listing and file reading tools
- [ ] Code analysis workflow
- [ ] Basic conversation flow

### Week 5-6: Code Agent
- [ ] Git operations (clone, branch, commit, push)
- [ ] Feature implementation workflow
- [ ] PR creation with description
- [ ] Error handling and edge cases

### Week 7-8: Jira Integration
- [ ] Jira API client
- [ ] Issue query tools
- [ ] Sprint/board overview
- [ ] Brainstorming workflow

### Week 9-10: Polish & Deploy
- [ ] Rich card responses
- [ ] Conversation memory
- [ ] Rate limiting
- [ ] Testing and documentation
- [ ] Deployment setup

---

## Future Enhancements

- **Multi-repo support**: Handle repos across multiple workspaces
- **CI/CD integration**: Trigger builds, check test results
- **Slack integration**: Extend to Slack workspaces
- **Code review automation**: Auto-review PRs for quality
- **Sprint planning**: AI-assisted sprint planning with Jira
- **Knowledge base**: Learn from past PRs and code patterns
- **Team analytics**: Code velocity, contribution metrics
- **Scheduled reports**: Daily/weekly status digests
