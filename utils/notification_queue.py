import json
import os
from datetime import datetime


class NotificationQueue:
    """Small durable outbox for notifications that fail after a local commit."""

    def __init__(self, data_dir):
        self.path = os.path.join(data_dir, "pending_notifications.json")

    def enqueue(self, webhook_url, recipients, subject, body, error):
        entries = self._load()
        entries.append({
            "queued_at": datetime.now().isoformat(timespec="seconds"),
            "webhook_url": webhook_url,
            "recipients": list(recipients),
            "subject": subject,
            "body": body,
            "last_error": error,
        })
        self._save(entries)

    def list_pending(self):
        return self._load()

    def remove(self, queued_at):
        entries = [item for item in self._load() if item.get("queued_at") != queued_at]
        self._save(entries)

    def _load(self):
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as source:
                data = json.load(source)
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def _save(self, entries):
        temporary_path = self.path + ".tmp"
        with open(temporary_path, "w", encoding="utf-8") as target:
            json.dump(entries, target, indent=2, ensure_ascii=False)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary_path, self.path)
