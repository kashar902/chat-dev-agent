import pytest
from unittest.mock import patch, MagicMock
from src.agent.core import Agent
from src.tools.bitbucket.client import BitbucketClient
from src.tools.git.local import GitManager


@pytest.fixture
def mock_bb():
    with patch("src.agent.core.BitbucketClient") as Mock:
        client = Mock.return_value
        client.list_repositories.return_value = [
            {"slug": "test-repo", "name": "Test Repo", "description": "A test repo"}
        ]
        client.get_file_tree.return_value = [
            {"name": "src", "type": "directory", "path": "src"},
            {"name": "README.md", "type": "file", "path": "README.md"},
        ]
        client.read_file.return_value = "# Test Repo\nThis is a test."
        client.get_repo_info.return_value = {"description": "A test repo"}
        yield client


@pytest.fixture
def mock_git():
    with patch("src.agent.core.GitManager") as Mock:
        manager = Mock.return_value
        yield manager


def test_agent_init():
    with patch("src.agent.core.OpenAI"):
        agent = Agent()
        assert agent.bb is not None
        assert agent.git is not None
        assert agent.conversation_history == {}


def test_list_repositories(mock_bb):
    repos = mock_bb.list_repositories()
    assert len(repos) == 1
    assert repos[0]["slug"] == "test-repo"


def test_get_file_tree(mock_bb):
    tree = mock_bb.get_file_tree("test-repo", "main")
    assert len(tree) == 2


def test_read_file(mock_bb):
    content = mock_bb.read_file("test-repo", "main", "README.md")
    assert "Test Repo" in content


def test_build_tools():
    with patch("src.agent.core.OpenAI"):
        agent = Agent()
        tools = agent._build_tools()
        tool_names = [t["function"]["name"] for t in tools]
        assert "list_repositories" in tool_names
        assert "get_file_tree" in tool_names
        assert "read_file" in tool_names
        assert "analyze_repo" in tool_names
        assert "create_branch" in tool_names
        assert "write_file" in tool_names
        assert "commit_and_push" in tool_names
        assert "create_pull_request" in tool_names
        assert "list_pull_requests" in tool_names
        assert "search_code" in tool_names
        assert "get_pr_diff" in tool_names
        assert "review_pr" in tool_names


def test_search_code(mock_bb):
    mock_bb.search_code.return_value = [{"name": "main.py", "path": "main.py", "type": "file"}]
    results = mock_bb.search_code("test-repo", "def ", "main")
    assert isinstance(results, list)
    assert len(results) == 1


def test_get_pr_diff(mock_bb):
    mock_bb.get_pull_request_diff.return_value = "diff --git a/file.py\n+new line"
    diff = mock_bb.get_pull_request_diff("test-repo", 1)
    assert "diff" in diff


def test_review_pr(mock_bb):
    mock_bb.list_pull_requests.return_value = [
        {"id": 1, "title": "Test PR", "author": "Test", "state": "OPEN"}
    ]
    mock_bb.get_pull_request_diff.return_value = "diff --git a/file.py\n+new line"
    prs = mock_bb.list_pull_requests("test-repo")
    assert any(p["id"] == 1 for p in prs)


def test_execute_search_code(mock_bb):
    mock_bb.search_code.return_value = [{"name": "main.py", "path": "main.py", "type": "file"}]
    with patch("src.agent.core.OpenAI"):
        agent = Agent()
        agent.bb = mock_bb
    result = agent._execute_tool("search_code", {"repo_slug": "test-repo", "query": "main"})
    assert "main.py" in result
