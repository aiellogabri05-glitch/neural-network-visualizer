from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    role: str
    content: str
    created_at: datetime


class SessionMemory:
    def __init__(self, max_messages=20):
        self.max_messages = max_messages
        self.messages = []

    def add(self, role, content):
        self.messages.append(Message(role=role, content=content, created_at=datetime.now()))
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def summary(self):
        if not self.messages:
            return "No session memory yet."

        lines = []
        for message in self.messages:
            time_label = message.created_at.strftime("%H:%M:%S")
            lines.append(f"[{time_label}] {message.role}: {message.content}")
        return "\n".join(lines)

