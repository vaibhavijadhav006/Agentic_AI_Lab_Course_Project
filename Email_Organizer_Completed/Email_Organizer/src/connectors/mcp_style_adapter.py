class MCPStyleEmailAdapter:
    """
    Adapter used by the agent's ToolRegistry.

    The important Lab-5 idea is that the agent does not directly know
    where email data comes from. It talks to a connector interface.
    """

    def __init__(self, connector):
        self.connector = connector

    def list_emails(self):
        return self.connector.call("email.list", {})

    def get_email(self, email_id):
        return self.connector.call("email.get", {"email_id": email_id})
