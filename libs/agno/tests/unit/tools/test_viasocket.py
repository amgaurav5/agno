from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("viasocket")

from viasocket import AgentTool

from agno.tools.viasocket import ViaSocketTools

SEND_SCHEMA = {
    "type": "object",
    "properties": {"text": {"type": "string", "description": "Message"}, "channel": {"type": "string"}},
    "required": ["text"],
}


def _tools():
    send = AgentTool(
        name="slack_send-message",
        description="Slack: Send a message.",
        parameters=SEND_SCHEMA,
        invoke=MagicMock(return_value='{"ok": true}'),
    )
    options = AgentTool(
        name="slack_list-options",
        description="Slack: look up ids.",
        parameters={"type": "object", "properties": {"field": {"type": "string"}}, "required": ["field"]},
        invoke=MagicMock(return_value='{"options": []}'),
    )
    return [send, options]


@patch("agno.tools.viasocket.agent_tools")
def test_registers_one_function_per_action_with_its_schema(mock_agent_tools):
    mock_agent_tools.return_value = _tools()
    client = MagicMock()

    toolkit = ViaSocketTools(user="user_123", apps=["slack"], actions={"slack": ["send-message"]}, viasocket=client)

    mock_agent_tools.assert_called_once_with(client, "user_123", ["slack"], {"slack": ["send-message"]})
    assert toolkit.name == "viasocket_tools"
    assert list(toolkit.functions) == ["slack_send-message", "slack_list-options"]
    send = toolkit.functions["slack_send-message"]
    assert send.description == "Slack: Send a message."
    assert send.parameters == SEND_SCHEMA


@patch("agno.tools.viasocket.agent_tools")
def test_calls_run_the_action_with_the_model_arguments(mock_agent_tools):
    tools = _tools()
    mock_agent_tools.return_value = tools
    toolkit = ViaSocketTools(user="user_123", apps=["slack"], viasocket=MagicMock())

    result = toolkit.functions["slack_send-message"].entrypoint(text="hi", channel="C1")

    assert result == '{"ok": true}'
    tools[0].invoke.assert_called_once_with({"text": "hi", "channel": "C1"})


@patch("agno.tools.viasocket.agent_tools")
def test_include_and_exclude_tools(mock_agent_tools):
    mock_agent_tools.return_value = _tools()
    only_send = ViaSocketTools(user="u", apps=["slack"], viasocket=MagicMock(), include_tools=["slack_send-message"])
    assert list(only_send.functions) == ["slack_send-message"]

    mock_agent_tools.return_value = _tools()
    no_options = ViaSocketTools(user="u", apps=["slack"], viasocket=MagicMock(), exclude_tools=["slack_list-options"])
    assert list(no_options.functions) == ["slack_send-message"]


@patch("agno.tools.viasocket.ViaSocket")
@patch("agno.tools.viasocket.agent_tools", return_value=[])
def test_client_is_built_from_the_environment(mock_agent_tools, mock_client):
    env = {"VIASOCKET_ORG_ID": "org", "VIASOCKET_PROJECT_ID": "proj", "VIASOCKET_EMBED_SECRET": "secret"}
    with patch.dict("os.environ", env):
        ViaSocketTools(user="u", apps=["slack"])

    mock_client.assert_called_once_with(org_id="org", project_id="proj", secret="secret")
