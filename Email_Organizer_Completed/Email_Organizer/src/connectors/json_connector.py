import json
from pathlib import Path
from typing import Dict, List


class JSONEmailConnector:
    """
    Lab 5: MCP-style connector.

    It exposes email capabilities through small, named operations.
    This version uses a JSON file so the project is easy to demonstrate.

    Later, the same interface can be replaced by an IMAP/Gmail connector
    without changing the agent or skills.
    """

    def __init__(self, path: Path):
        self.path = path

    def list_tools(self):
        return [
            {
                "name": "email.list",
                "description": "List emails from the connected email source.",
                "input_schema": {"type": "object", "properties": {}}
            },
            {
                "name": "email.get",
                "description": "Get one email by ID.",
                "input_schema": {
                    "type": "object",
                    "properties": {"email_id": {"type": "string"}},
                    "required": ["email_id"]
                }
            },
            {
                "name": "email.save_draft",
                "description": "Save a draft; never sends an email.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "email_id": {"type": "string"},
                        "to": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"}
                    },
                    "required": ["email_id", "to", "subject", "body"]
                }
            }
        ]

    def call(self, tool_name: str, arguments: Dict):
        if tool_name == "email.list":
            return self.list_emails()
        if tool_name == "email.get":
            return self.get_email(arguments["email_id"])
        if tool_name == "email.save_draft":
            # Deliberately does not send.
            return {
                "status": "draft_saved",
                "approval_required": True,
                "message": "Draft operation is simulated in Lab 5."
            }
        raise ValueError(f"Unknown connector tool: {tool_name}")

    def list_emails(self) -> List[Dict]:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_email(self, email_id: str) -> Dict:
        for email in self.list_emails():
            if email["id"] == email_id:
                return email
        raise KeyError(f"Email {email_id} not found")
