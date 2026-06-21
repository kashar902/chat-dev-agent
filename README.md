# Google Chat AI Agent

An AI-powered software engineering assistant that lives in Google Chat. It can analyze Bitbucket repositories, implement features from natural language instructions, and create Pull Requests — all from a chat message.

## Features

- **Repository Analysis** — Understand project structure, tech stack, and code patterns
- **Code Reading** — Browse and read files across your Bitbucket workspace
- **Feature Implementation** — Describe what you want; the agent writes code and opens a PR
- **PR Management** — List and review open Pull Requests
- **Branch & Commit** — Creates branches, commits changes, and pushes to remote
- **Conversation Memory** — Maintains context within a chat thread

## Architecture

```
Google Chat Space
       │ Webhook
       ▼
  FastAPI Server  ───  Agent Core (OpenAI GPT-4o)
       │                    │
       ▼                    ▼
  Google Chat API    Tool Layer
                   ┌───────┴───────┐
                Bitbucket       Git (local)
                 API client      operations
```

## Project Structure

```
├── src/
│   ├── server/app.py           # FastAPI webhook endpoints
│   ├── agent/core.py           # Agent orchestration + OpenAI tool calling
│   ├── tools/
│   │   ├── bitbucket/client.py # Bitbucket REST API client
│   │   └── git/local.py        # Local git clone/branch/commit/push
│   ├── integrations/
│   │   └── google_chat.py      # Message parsing & response builders
│   ├── config.py               # Settings via pydantic-settings
│   └── utils/logger.py         # Logging setup
├── prompts/
│   ├── system.md               # Base system prompt
│   ├── code_analysis.md        # Code analysis prompt
│   └── feature_impl.md         # Feature implementation prompt
├── tests/
│   └── test_agent.py           # Unit tests
├── doc/
│   └── implementation-plan.md  # Full implementation plan
├── main.py                     # Entry point
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Prerequisites

- Python 3.11+
- Git
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [Bitbucket App Password](https://support.atlassian.com/bitbucket-cloud/docs/create-an-app-password/) with repository read/write access
- A Google Chat space with webhook configured

## Setup

### 1. Clone and install

```bash
git clone <your-repo-url>
cd "Agent for the google chat space"
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
OPENAI_API_KEY=sk-your-key-here
BITBUCKET_WORKSPACE=your-workspace
BITBUCKET_USERNAME=your-username
BITBUCKET_APP_PASSWORD=your-app-password
GOOGLE_CHAT_SPACE_ID=spaces/your-space-id
REPOS_DIR=./repos
```

### 3. Run locally

```bash
python main.py
```

The server starts at `http://localhost:8000`.

### 4. Run with Docker

```bash
docker compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhook/google-chat` | Google Chat webhook handler |
| `POST` | `/webhook/test` | Test the agent without Google Chat |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

### Test the agent directly

```bash
curl -X POST http://localhost:8000/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"message": "list my repositories"}'
```

## Usage in Google Chat

Once the webhook is configured, mention the bot in your Google Chat space:

- `analyze backend-api` — Analyze repository structure and tech stack
- `read backend-api src/auth.py` — Read a specific file
- `implement password reset in auth module` — Implement a feature and open a PR
- `pr list` — List open Pull Requests
- `pr review 123` — Review a specific PR

## Running Tests

```bash
pytest tests/ -v
```

## How It Works

1. A user sends a message in Google Chat mentioning the bot
2. The webhook receives the event and parses the message
3. The Agent sends the message to OpenAI with available tool definitions
4. The LLM decides which tools to call (list repos, read files, create branches, etc.)
5. Results are fed back to the LLM in a loop until it produces a final response
6. The response is sent back to the Google Chat thread

## License

MIT
