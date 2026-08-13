import logging
import requests
from typing import Dict, Any, List, Optional
from src.config import settings

logger = logging.getLogger(__name__)

class ClickUpService:
    """
    Service to manage ClickUp tasks/tickets (acting as Jira alternative).
    Includes automatic dry-run mock fallback if API key or List ID is not configured.
    """

    def __init__(self):
        self.api_key = settings.CLICKUP_API_KEY
        self.list_id = settings.CLICKUP_LIST_ID
        self.base_url = "https://api.clickup.com/api/v2"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.list_id and not self.api_key.startswith("pk_123"))

    def create_task(self, title: str, description: str, priority: int = 3) -> Dict[str, Any]:
        """
        Creates a ticket in ClickUp.
        """
        if not self.is_configured():
            mock_id = f"mock-cu-{abs(hash(title)) % 100000}"
            mock_url = f"https://app.clickup.com/t/{mock_id}"
            logger.info(f"[ClickUp Service - Mock Mode] Created ClickUp task '{title}' (ID: {mock_id})")
            return {
                "id": mock_id,
                "name": title,
                "description": description,
                "status": "to do",
                "url": mock_url,
                "mode": "mock"
            }

        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
        url = f"{self.base_url}/list/{self.list_id}/task"
        payload = {
            "name": title,
            "description": description,
            "status": "to do",
            "priority": priority,
            "tags": ["agentic-ai", "automated-task"]
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code in (200, 201):
                data = response.json()
                logger.info(f"[ClickUp Service] Successfully created task '{title}' -> ID: {data.get('id')}")
                return {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "description": data.get("description"),
                    "status": data.get("status", {}).get("status", "to do"),
                    "url": data.get("url", f"https://app.clickup.com/t/{data.get('id')}"),
                    "mode": "live"
                }
            else:
                logger.error(f"[ClickUp Service] Failed to create task: {response.status_code} - {response.text}")
        except Exception as e:
            logger.exception(f"[ClickUp Service] Exception while creating ClickUp task: {e}")

        # Fallback if request failed
        mock_id = f"fallback-cu-{abs(hash(title)) % 10000}"
        return {
            "id": mock_id,
            "name": title,
            "description": description,
            "status": "to do",
            "url": f"https://app.clickup.com/t/{mock_id}",
            "mode": "fallback"
        }

    def update_task_status(self, task_id: str, status: str = "complete") -> bool:
        """
        Updates task status in ClickUp.
        """
        if not self.is_configured() or "mock" in task_id or "fallback" in task_id:
            logger.info(f"[ClickUp Service - Mock Mode] Updated task {task_id} status to '{status}'")
            return True

        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
        url = f"{self.base_url}/task/{task_id}"
        payload = {"status": status}

        try:
            res = requests.put(url, json=payload, headers=headers, timeout=10)
            return res.status_code == 200
        except Exception as e:
            logger.error(f"[ClickUp Service] Failed updating task status: {e}")
            return False

# Global singleton instance
clickup_service = ClickUpService()
