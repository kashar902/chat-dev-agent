# Documentation

## Files

- **implementation-plan.md** - Complete implementation plan for the Google Chat AI Agent

## Quick Navigation

| Section | What It Covers |
|---------|----------------|
| [Project Overview](implementation-plan.md#1-project-overview) | What the agent does, target users |
| [Architecture](implementation-plan.md#2-architecture) | System design, component breakdown, message flow |
| [Phase 1: Bitbucket](implementation-plan.md#3-phase-1-bitbucket-code-agent) | Repo analysis, code understanding, feature implementation, PR creation |
| [Phase 2: Jira](implementation-plan.md#4-phase-2-jira-integration) | Sprint status, backlog queries, brainstorming |
| [Google Chat Integration](implementation-plan.md#5-google-chat-integration) | Webhook setup, message handling, bot commands |
| [API Keys & Secrets](implementation-plan.md#6-api-keys--secrets) | Required credentials and security notes |
| [Project Structure](implementation-plan.md#7-project-structure) | Directory layout and file organization |
| [Dependencies](implementation-plan.md#8-dependencies) | Python packages and system requirements |
| [Deployment](implementation-plan.md#9-deployment) | Docker, Cloud Run, VM deployment options |
| [Testing](implementation-plan.md#10-testing-strategy) | Unit, integration, and manual test plans |
| [Implementation Priority](implementation-plan.md#implementation-priority) | 10-week roadmap |
| [Future Enhancements](implementation-plan.md#future-enhancements) | Planned improvements |

## Agent Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `analyze <repo>` | Analyze repository structure | `analyze backend-api` |
| `search <repo> <query>` | Search code for patterns | `search backend-api def login` |
| `read <repo> <file>` | Read a specific file | `read backend-api src/auth.py` |
| `implement <feature>` | Implement a feature + create PR | `implement password reset in auth` |
| `pr list` | List open pull requests | `pr list` |
| `pr review <id>` | Review a PR with detailed feedback | `pr review 123` |
| `jira status <ticket>` | Get Jira ticket status | `jira status PROJ-123` |
| `jira sprint` | Show current sprint | `jira sprint` |
| `jira backlog` | Show project backlog | `jira backlog` |
| `brainstorm <topic>` | Brainstorm features with context | `brainstorm auth improvements` |
| `help` | Show available commands | `help` |

## Phase Timeline

- **Phase 1** (Weeks 1-6): Bitbucket Code Agent
- **Phase 2** (Weeks 7-8): Jira Integration
- **Phase 3** (Weeks 9-10): Polish & Deployment
