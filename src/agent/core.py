import json
import re
from openai import OpenAI
from src.config import settings
from src.tools.bitbucket.client import BitbucketClient
from src.tools.git.local import GitManager
from src.utils.logger import logger
from pathlib import Path


PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


class Agent:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.bb = BitbucketClient()
        self.git = GitManager()
        self.conversation_history: dict[str, list] = {}

    def _get_history(self, thread_id: str) -> list[dict]:
        if thread_id not in self.conversation_history:
            self.conversation_history[thread_id] = []
        return self.conversation_history[thread_id]

    def _build_tools(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_repositories",
                    "description": "List all Bitbucket repositories in the workspace",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_file_tree",
                    "description": "Get directory structure of a repository",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_slug": {"type": "string", "description": "Repository name"},
                            "branch": {"type": "string", "description": "Branch name", "default": "main"},
                            "path": {"type": "string", "description": "Subdirectory path", "default": ""},
                        },
                        "required": ["repo_slug"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a file in a repository",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_slug": {"type": "string", "description": "Repository name"},
                            "branch": {"type": "string", "description": "Branch name", "default": "main"},
                            "file_path": {"type": "string", "description": "Path to the file"},
                        },
                        "required": ["repo_slug", "file_path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_repo",
                    "description": "Analyze repository structure, tech stack, and patterns",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_slug": {"type": "string", "description": "Repository name"},
                            "branch": {"type": "string", "description": "Branch name", "default": "main"},
                        },
                        "required": ["repo_slug"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_branch",
                    "description": "Create a new git branch in a repository",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_slug": {"type": "string", "description": "Repository name"},
                            "branch_name": {"type": "string", "description": "New branch name"},
                        },
                        "required": ["repo_slug", "branch_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file in a repository",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_slug": {"type": "string", "description": "Repository name"},
                            "file_path": {"type": "string", "description": "Path to write to"},
                            "content": {"type": "string", "description": "File content"},
                        },
                        "required": ["repo_slug", "file_path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "commit_and_push",
                    "description": "Commit all changes and push to remote",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_slug": {"type": "string", "description": "Repository name"},
                            "branch": {"type": "string", "description": "Branch to push"},
                            "message": {"type": "string", "description": "Commit message"},
                        },
                        "required": ["repo_slug", "branch", "message"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_pull_request",
                    "description": "Create a Pull Request on Bitbucket",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_slug": {"type": "string", "description": "Repository name"},
                            "source_branch": {"type": "string", "description": "Source branch"},
                            "dest_branch": {"type": "string", "description": "Destination branch", "default": "main"},
                            "title": {"type": "string", "description": "PR title"},
                            "description": {"type": "string", "description": "PR description"},
                        },
                        "required": ["repo_slug", "source_branch", "title"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_pull_requests",
                    "description": "List open Pull Requests in a repository",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_slug": {"type": "string", "description": "Repository name"},
                        },
                        "required": ["repo_slug"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_code",
                    "description": "Search for code patterns across a repository (e.g. function names, classes, imports)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_slug": {"type": "string", "description": "Repository name"},
                            "query": {"type": "string", "description": "Search query"},
                            "branch": {"type": "string", "description": "Branch name", "default": "main"},
                        },
                        "required": ["repo_slug", "query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_pr_diff",
                    "description": "Get the diff of a Pull Request to review changes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_slug": {"type": "string", "description": "Repository name"},
                            "pr_id": {"type": "integer", "description": "Pull Request ID"},
                        },
                        "required": ["repo_slug", "pr_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "review_pr",
                    "description": "Review a Pull Request: fetch its diff, analyze the changes, and provide feedback on code quality, bugs, and suggestions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo_slug": {"type": "string", "description": "Repository name"},
                            "pr_id": {"type": "integer", "description": "Pull Request ID"},
                        },
                        "required": ["repo_slug", "pr_id"],
                    },
                },
            },
        ]

    def _execute_tool(self, name: str, args: dict) -> str:
        try:
            if name == "list_repositories":
                repos = self.bb.list_repositories()
                return json.dumps(repos, indent=2)

            elif name == "get_file_tree":
                tree = self.bb.get_file_tree(
                    args["repo_slug"], args.get("branch", "main"), args.get("path", "")
                )
                return json.dumps(tree, indent=2)

            elif name == "read_file":
                content = self.bb.read_file(
                    args["repo_slug"], args.get("branch", "main"), args["file_path"]
                )
                return content[:5000]

            elif name == "analyze_repo":
                return self._analyze_repo(args["repo_slug"], args.get("branch", "main"))

            elif name == "create_branch":
                self.git.get_or_clone(args["repo_slug"])
                self.git.create_branch(args["repo_slug"], args["branch_name"])
                return f"Branch '{args['branch_name']}' created successfully"

            elif name == "write_file":
                self.git.write_file(args["repo_slug"], args["file_path"], args["content"])
                return f"File '{args['file_path']}' written successfully"

            elif name == "commit_and_push":
                self.git.commit(args["repo_slug"], args["message"])
                self.git.push(args["repo_slug"], args["branch"])
                return f"Changes committed and pushed to '{args['branch']}'"

            elif name == "create_pull_request":
                pr = self.bb.create_pull_request(
                    args["repo_slug"],
                    args["source_branch"],
                    args.get("dest_branch", "main"),
                    args["title"],
                    args.get("description", ""),
                )
                return json.dumps({
                    "pr_id": pr["id"],
                    "url": pr["links"]["html"]["href"],
                    "title": pr["title"],
                }, indent=2)

            elif name == "list_pull_requests":
                prs = self.bb.list_pull_requests(args["repo_slug"])
                return json.dumps(prs, indent=2)

            elif name == "search_code":
                results = self.bb.search_code(
                    args["repo_slug"], args["query"], args.get("branch", "main")
                )
                return json.dumps(results, indent=2)

            elif name == "get_pr_diff":
                diff = self.bb.get_pull_request_diff(args["repo_slug"], args["pr_id"])
                return diff[:8000]

            elif name == "review_pr":
                return self._review_pr(args["repo_slug"], args["pr_id"])

            return f"Unknown tool: {name}"
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return f"Error: {str(e)}"

    def _analyze_repo(self, repo_slug: str, branch: str = "main") -> str:
        analysis_prompt = load_prompt("code_analysis")
        try:
            tree = self.bb.get_file_tree(repo_slug, branch)
            tree_str = "\n".join(
                f"{'[DIR]' if e['type'] == 'directory' else '[FILE]'} {e['path']}"
                for e in tree
            )
        except Exception:
            tree_str = "Could not fetch file tree"

        try:
            info = self.bb.get_repo_info(repo_slug)
            readme = ""
            try:
                readme = self.bb.read_file(repo_slug, branch, "README.md")[:2000]
            except Exception:
                pass
            pkg_files = {}
            for pkg in ["package.json", "requirements.txt", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml"]:
                try:
                    pkg_files[pkg] = self.bb.read_file(repo_slug, branch, pkg)[:1000]
                except Exception:
                    pass
        except Exception as e:
            return f"Error analyzing repo: {e}"

        files_str = "\n---\n".join(f"=== {k} ===\n{v}" for k, v in pkg_files.items())
        return f"""## Repository Analysis: {repo_slug}

**Description**: {info.get('description', 'N/A')}

### File Tree
{tree_str}

### README (excerpt)
{readme if readme else 'No README found'}

### Dependency Files
{files_str if pkg_files else 'No dependency files found'}
"""

    def _review_pr(self, repo_slug: str, pr_id: int) -> str:
        review_prompt = load_prompt("code_review")
        try:
            prs = self.bb.list_pull_requests(repo_slug)
            pr = next((p for p in prs if p["id"] == pr_id), None)
            if not pr:
                return f"PR #{pr_id} not found or not open"
        except Exception:
            pr = {"id": pr_id, "title": "Unknown", "author": "Unknown"}

        try:
            diff = self.bb.get_pull_request_diff(repo_slug, pr_id)
            if not diff.strip():
                return "No changes found in this PR."
        except Exception as e:
            return f"Error fetching diff: {e}"

        try:
            readme = ""
            tree = self.bb.get_file_tree(repo_slug)
            paths = [e["path"] for e in tree if e["type"] == "file"]
            for candidate in ["README.md", "requirements.txt", "package.json"]:
                if candidate in paths:
                    try:
                        readme += f"\n=== {candidate} ===\n"
                        readme += self.bb.read_file(repo_slug, "main", candidate)[:1000]
                    except Exception:
                        pass
        except Exception:
            readme = ""

        messages = [
            {"role": "system", "content": review_prompt},
            {"role": "user", "content": f"""Review this Pull Request.

## PR #{pr['id']}: {pr.get('title', 'N/A')}
Author: {pr.get('author', 'Unknown')}

## Diff
```diff
{diff[:6000]}
```

## Project Context
{readme if readme else 'N/A'}
"""},
        ]

        try:
            response = self.client.chat.completions.create(
                model=settings.model_name,
                messages=messages,
            )
            return response.choices[0].message.content or "No review generated."
        except Exception as e:
            return f"Error generating review: {e}"

    def process(self, message: str, thread_id: str = "default") -> str:
        system_prompt = load_prompt("system")
        history = self._get_history(thread_id)
        history.append({"role": "user", "content": message})

        messages = [{"role": "system", "content": system_prompt}] + history[-20:]
        tools = self._build_tools()

        logger.info(f"Processing message in thread {thread_id}: {message[:100]}")

        while True:
            response = self.client.chat.completions.create(
                model=settings.model_name,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )

            choice = response.choices[0]

            if choice.finish_reason == "stop":
                reply = choice.message.content or ""
                history.append({"role": "assistant", "content": reply})
                return reply

            if choice.finish_reason == "tool_calls":
                messages.append(choice.message)
                for tool_call in choice.message.tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments)
                    logger.info(f"Calling tool: {fn_name}({fn_args})")
                    result = self._execute_tool(fn_name, fn_args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
                continue

            return "Error: unexpected response from LLM"
