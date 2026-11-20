"""
viaSocket Tools
=============================

Demonstrates an agent acting in the apps an end user connected through viaSocket.

Setup:
1. pip install agno openai viasocket
2. Create an embed project at https://flow.viasocket.com and export VIASOCKET_ORG_ID,
   VIASOCKET_PROJECT_ID and VIASOCKET_EMBED_SECRET, plus OPENAI_API_KEY.
3. Connect Slack for the user once: npx viasocket-apps connect slack --user user_123
"""

from agno.agent import Agent
from agno.tools.viasocket import ViaSocketTools

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------

# One tool per chosen action, run on user_123's own Slack connection.
# A picker field (like a channel) comes with a slack_list-options tool to look up its id.
agent = Agent(
    tools=[
        ViaSocketTools(
            user="user_123",
            apps=["slack"],
            actions={"slack": ["send-message"]},
        )
    ],
    markdown=True,
)

# ---------------------------------------------------------------------------
# Run Agent
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent.print_response("Post 'Q3 numbers are in' in the #general channel", stream=True)
