from os import getenv
from typing import Any, Dict, List, Optional

from agno.tools import Toolkit
from agno.tools.function import Function
from agno.utils.log import log_debug

try:
    from viasocket import ViaSocket, agent_tools
except ImportError:
    raise ImportError("`viasocket` not installed. Please install using `pip install viasocket`.")


class ViaSocketTools(Toolkit):
    """Actions in the apps an end user connected through viaSocket (Slack, Google Sheets, HubSpot, Notion and
    2,300+ more), one tool per action, each run on that user's own connection.

    Args:
        user (str): Your id for the end user whose connected apps the tools act in.
        apps (List[str]): App slugs, e.g. ["slack", "google-sheets"].
        actions (Optional[Dict[str, List[str]]]): Per app, the actions to expose, e.g. {"slack": ["send-message"]}.
            Defaults to every published action of each app.
        viasocket (Optional[ViaSocket]): A ready client. Otherwise one is built from org_id, project_id and secret.
        org_id (Optional[str]): viaSocket org id. Defaults to VIASOCKET_ORG_ID.
        project_id (Optional[str]): viaSocket embed project id. Defaults to VIASOCKET_PROJECT_ID.
        secret (Optional[str]): viaSocket embed secret. Defaults to VIASOCKET_EMBED_SECRET.
    """

    def __init__(
        self,
        user: str,
        apps: List[str],
        actions: Optional[Dict[str, List[str]]] = None,
        viasocket: Optional[ViaSocket] = None,
        org_id: Optional[str] = None,
        project_id: Optional[str] = None,
        secret: Optional[str] = None,
        **kwargs: Any,
    ):
        self.viasocket = viasocket or ViaSocket(
            org_id=org_id or getenv("VIASOCKET_ORG_ID"),
            project_id=project_id or getenv("VIASOCKET_PROJECT_ID"),
            secret=secret or getenv("VIASOCKET_EMBED_SECRET"),
        )
        # The action's own JSON Schema goes to the model as is, so the entrypoint is not inspected.
        functions = [
            Function(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters,
                entrypoint=self._caller(tool.invoke),
                skip_entrypoint_processing=True,
            )
            for tool in agent_tools(self.viasocket, user, apps, actions)
        ]
        # The names are known only now, so the toolkit can check include_tools / exclude_tools against them.
        super().__init__(name="viasocket_tools", tools=functions, auto_register=False, **kwargs)
        for f in functions:
            if self.include_tools is not None and f.name not in self.include_tools:
                continue
            if self.exclude_tools is not None and f.name in self.exclude_tools:
                continue
            f.requires_confirmation = f.name in self.requires_confirmation_tools
            f.external_execution = f.name in self.external_execution_required_tools
            f.stop_after_tool_call = f.name in self.stop_after_tool_call_tools
            f.show_result = f.name in self.show_result_tools or f.stop_after_tool_call
            self.functions[f.name] = f
            log_debug(f"Function: {f.name} registered with {self.name}")

    @staticmethod
    def _caller(invoke: Any) -> Any:
        def run(**kwargs: Any) -> str:
            # Errors come back as a sentence for the model, so one bad call does not end the run.
            return invoke(kwargs)

        return run
